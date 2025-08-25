"""
报告汇总师智能体

基于OxyGent ReActAgent的报告汇总师，优化并行调用多个分析师生成最终报告
使用智能错误处理系统确保稳定性
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from oxygent import oxy
from prompts import reporter_prompts
from utils.oxygent_error_handler import get_agent_factory
from loguru import logger


class Reporter:
    """报告汇总师 - 基于ReActAgent，优化并行处理"""
    
    @staticmethod
    def create_agent():
        """创建报告汇总师智能体
        
        使用OxyGent框架的子智能体机制，让框架处理并行调用和错误重试
        """
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        config = factory.create_react_agent_config(
            name="reporter",
            desc="专业的报告撰写员，整合多个分析师的评价生成综合报告，并提供下载链接",
            prompt=reporter_prompts.SYSTEM_PROMPT,
            sub_agents=["text_analyst", "praiser", "guide"],
            max_react_rounds=2,  # 限制ReAct轮数，避免无限循环
            retries=2,           # 最多重试2次
            timeout=180,         # 180秒超时（需要协调多个子智能体）
            semaphore=1,         # 限制并发数量
        )
        
        return oxy.ReActAgent(**config)  # type: ignore
    
    @staticmethod
    def generate_report_files(
        report_content: str,
        essay_info: Dict[str, Any],
        base_filename: Optional[str] = None
    ) -> Dict[str, str]:
        """
        生成Markdown和HTML格式的报告文件
        
        Args:
            report_content: 报告内容（Markdown格式）
            essay_info: 作文信息（学生姓名、题目等）
            base_filename: 基础文件名，如果不提供则自动生成
            
        Returns:
            包含文件路径和下载链接的字典
        """
        try:
            # 确保 reports 目录存在
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            if not base_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                student_name = essay_info.get("student_name", "学生")
                essay_title = essay_info.get("essay_title", "作文")
                base_filename = f"{student_name}_{essay_title}_{timestamp}"
            
            # 清理文件名中的特殊字符
            safe_filename = "".join(c for c in base_filename if c.isalnum() or c in "._- ")
            
            markdown_path = reports_dir / f"{safe_filename}.md"
            html_path = reports_dir / f"{safe_filename}.html"
            
            # 保存Markdown文件
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            # 生成HTML文件
            html_content = Reporter._markdown_to_html(report_content, essay_info)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # 生成下载链接
            markdown_url = f"http://127.0.0.1:8081/reports/{safe_filename}.md"
            html_url = f"http://127.0.0.1:8081/reports/{safe_filename}.html"
            
            logger.info(f"报告文件已生成: {markdown_path}, {html_path}")
            logger.info(f"报告下载链接: {markdown_url}, {html_url}")
            
            return {
                "markdown_path": str(markdown_path),
                "html_path": str(html_path),
                "markdown_url": markdown_url,
                "html_url": html_url,
                "download_links_text": Reporter.create_download_links({
                    "markdown_url": markdown_url,
                    "html_url": html_url
                }, essay_info)
            }
            
        except Exception as e:
            logger.error(f"生成报告文件时发生错误: {str(e)}")
            return {}
            
    
    @staticmethod
    def _markdown_to_html(markdown_content: str, essay_info: Dict[str, Any]) -> str:
        """
        将Markdown内容转换为HTML格式
        """
        # 简单的Markdown到HTML转换
        html_content = markdown_content
        
        # 转换标题
        import re
        html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
        html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
        
        # 转换加粗文本
        html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_content)
        
        # 转换列表
        lines = html_content.split('\n')
        in_list = False
        processed_lines = []
        
        for line in lines:
            if line.strip().startswith('- '):
                if not in_list:
                    processed_lines.append('<ul>')
                    in_list = True
                processed_lines.append(f'<li>{line.strip()[2:]}</li>')
            else:
                if in_list:
                    processed_lines.append('</ul>')
                    in_list = False
                processed_lines.append(line)
        
        if in_list:
            processed_lines.append('</ul>')
        
        html_content = '\n'.join(processed_lines)
        
        # 转换段落
        html_content = re.sub(r'\n\n', '</p>\n<p>', html_content)
        html_content = f'<p>{html_content}</p>'
        
        # 创建完整的HTML页面
        full_html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>作文评价报告 - {essay_info.get('student_name', '学生')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .report-container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        ul {{
            padding-left: 20px;
        }}
        li {{
            margin: 5px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        {html_content}
        <div class="footer">
            <p>📚 AI作文评审小组 | 生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
        
        return full_html
    
    @staticmethod
    def create_download_links(file_paths: Dict[str, str], essay_info: Dict[str, Any]) -> str:
        """
        创建下载链接的显示文本
        """
        if not file_paths:
            return ""
        
        student_name = essay_info.get('student_name', '学生')
        essay_title = essay_info.get('essay_title', '作文')
        
        links_text = f"""

📋 **评价报告已生成完成！**

👤 学生：{student_name} | 📝 作文：《{essay_title}》

📥 **下载链接：**
- 📄 [查看Markdown版本]({file_paths.get('markdown_url', '#')}) 
- 🌐 [查看HTML版本]({file_paths.get('html_url', '#')})

💡 **使用说明：**
- Markdown版本：适合编辑和打印
- HTML版本：带样式的完整报告，推荐在浏览器中查看

✨ 点击链接即可在新窗口打开报告！
"""
        return links_text


# 导出智能体创建函数
def get_reporter():
    """获取报告汇总师智能体"""
    agent = Reporter.create_agent()
    
    # 增强智能体，确保在生成报告后返回下载链接
    original_report_function = None
    
    # 处理agent.tools可能是列表的情况
    if hasattr(agent.tools, 'get'):
        # 如果tools是字典
        original_report_function = agent.tools.get("generate_report")
        
        if original_report_function:
            def enhanced_report_function(*args, **kwargs):
                result = original_report_function(*args, **kwargs)
                if isinstance(result, dict) and "download_links_text" in result:
                    # 确保下载链接被包含在最终回复中
                    logger.info(f"返回报告下载链接: {result['download_links_text']}")
                return result
            
            agent.tools["generate_report"] = enhanced_report_function
    elif isinstance(agent.tools, list):
        # 如果tools是列表，不执行增强逻辑
        logger.info("agent.tools是列表类型，跳过工具增强")
    
    return agent