"""
文本分析师智能体

基于OxyGent ChatAgent + langextract的实现
"""

import asyncio
import textwrap
from typing import Dict, List, Any, Optional

import langextract as lx
from loguru import logger
from oxygent import oxy, OxyRequest
from oxygent.utils.env_utils import get_env_var

from prompts.analyst_prompts import SYSTEM_PROMPT, LANGEXTRACT_ANALYSIS_PROMPT
from langextract_schemas.schema_templates import SchemaTemplateManager, ExtractionTemplate, EssayType, GradeLevel


def create_text_analyst_agent() -> oxy.ChatAgent:
    """
    创建文本分析师智能体
    
    基于OxyGent ChatAgent + langextract的集成实现
    """
    return oxy.ChatAgent(  # type: ignore
        name="text_analyst",
        desc="严谨的文本分析专家，使用langextract进行深度结构化分析",
        prompt=SYSTEM_PROMPT
    )


def process_analysis_input(oxy_request: OxyRequest) -> OxyRequest:
    """
    处理文本分析输入请求
    
    集成langextract功能到OxyGent工作流中
    """
    try:
        # 获取用户查询
        user_query = oxy_request.get_query(master_level=True)
        current_query = oxy_request.get_query()
        
        # 如果查询中包含作文分析任务，进行预处理
        if "分析作文" in current_query or "文本分析" in current_query:
            helper = TextAnalystHelper()
            
            # 提取作文内容（假设在arguments中）
            essay_content = oxy_request.arguments.get("essay_content", "")
            essay_type = oxy_request.arguments.get("essay_type", "narrative")
            grade_level = oxy_request.arguments.get("grade_level", "grade_3")
            
            if essay_content:
                # 异步执行分析（在实际使用中会被OxyGent框架处理）
                analysis_prompt = helper.prepare_analysis_prompt(
                    essay_content, essay_type, grade_level
                )
                oxy_request.set_query(analysis_prompt)
        
        return oxy_request
        
    except Exception as e:
        logger.error(f"处理分析输入失败: {e}")
        return oxy_request


class TextAnalystHelper:
    """
    文本分析师辅助类
    
    提供langextract集成和数据处理功能
    """
    
    def __init__(self):
        self.schema_manager = SchemaTemplateManager()
        self.name = "text_analyst_helper"
        self.description = "文本分析辅助工具，处理langextract集成"
    
    def prepare_analysis_prompt(
        self,
        essay_content: str,
        essay_type: str,
        grade_level: str,
        schema_template: Optional[ExtractionTemplate] = None
    ) -> str:
        """
        准备分析提示词
        
        Args:
            essay_content: 作文内容
            essay_type: 作文类型
            grade_level: 年级水平
            schema_template: 指定的评价模板
            
        Returns:
            格式化的分析提示词
        """
        try:
            # 获取合适的提取模板
            if not schema_template:
                # 转换字符串参数为枚举类型
                essay_type_enum = EssayType(essay_type) if essay_type in [e.value for e in EssayType] else EssayType.NARRATIVE
                grade_level_enum = GradeLevel(grade_level) if grade_level in [g.value for g in GradeLevel] else GradeLevel.GRADE_3
                
                schema_template = self.schema_manager.get_template_by_type(
                    essay_type_enum, grade_level_enum
                )
            
            # 格式化提示词
            formatted_prompt = LANGEXTRACT_ANALYSIS_PROMPT.format(
                essay_content=essay_content,
                schema_description=schema_template.prompt
            )
            
            return formatted_prompt
            
        except Exception as e:
            logger.error(f"准备分析提示词失败: {e}")
            return f"请分析以下作文：\n{essay_content}"
    
    async def analyze_essay(
        self,
        essay_content: str,
        essay_type: str,
        grade_level: str,
        schema_template: Optional[ExtractionTemplate] = None
    ) -> Dict[str, Any]:
        """
        分析作文内容
        
        Args:
            essay_content: 作文内容
            essay_type: 作文类型
            grade_level: 年级水平
            schema_template: 指定的评价模板
            
        Returns:
            结构化分析结果
        """
        logger.info(f"开始分析作文，类型: {essay_type}, 年级: {grade_level}")
        
        try:
            # 获取合适的提取模板
            if not schema_template:
                # 转换字符串参数为枚举类型
                essay_type_enum = EssayType(essay_type) if essay_type in [e.value for e in EssayType] else EssayType.NARRATIVE
                grade_level_enum = GradeLevel(grade_level) if grade_level in [g.value for g in GradeLevel] else GradeLevel.GRADE_3
                
                schema_template = self.schema_manager.get_template_by_type(
                    essay_type_enum, grade_level_enum
                )
            
            # 使用langextract进行结构化提取
            extraction_result = await self._perform_langextract_analysis(
                essay_content, schema_template
            )
            
            # 整理分析结果
            analysis_result = self._organize_analysis_result(
                extraction_result, essay_content
            )
            
            logger.info("作文分析完成")
            return analysis_result
            
        except Exception as e:
            logger.error(f"作文分析失败: {e}")
            return self._get_fallback_analysis(essay_content)
    
    async def _perform_langextract_analysis(
        self,
        text: str,
        template: ExtractionTemplate
    ) -> lx.data.AnnotatedDocument:
        """
        执行langextract分析
        """
        try:
            # 从环境变量获取配置
            api_key = get_env_var("LANGEXTRACT_API_KEY") or get_env_var("DEFAULT_LLM_API_KEY")
            model_id = get_env_var("LANGEXTRACT_MODEL_ID") or get_env_var("DEFAULT_LLM_MODEL_NAME") or "gemini-2.5-flash"
            base_url = get_env_var("LANGEXTRACT_BASE_URL") or get_env_var("DEFAULT_LLM_BASE_URL")
            
            # 构建基础参数
            extract_kwargs = {
                "text_or_documents": text,
                "prompt_description": template.prompt,
                "examples": template.examples,
                "model_id": model_id,
                "extraction_passes": 2,  # 多次提取提高准确性
                "max_workers": 4,
                "max_char_buffer": 2000  # 适合作文长度的缓冲区
            }
            
            # 如果有API密钥，添加到参数中
            if api_key:
                extract_kwargs["api_key"] = api_key
            
            # 检查是否使用第三方OpenAI兼容API
            if base_url and base_url != "https://api.openai.com/v1":
                logger.info(f"使用第三方OpenAI兼容API: {base_url}")
                # 使用OpenAI语言模型类型，并通过language_model_params传递base_url
                extract_kwargs["language_model_type"] = lx.inference.OpenAILanguageModel
                extract_kwargs["language_model_params"] = {
                    "base_url": base_url
                }
                # OpenAI模型需要特定参数
                extract_kwargs["fence_output"] = True
                extract_kwargs["use_schema_constraints"] = False
            else:
                logger.info("使用默认langextract配置")
            
            result = lx.extract(**extract_kwargs)
            
            # 处理结果，可能是单个文档或文档列表
            if isinstance(result, list) and len(result) > 0:
                document = result[0]  # type: ignore
            elif hasattr(result, '__iter__') and not isinstance(result, str):
                # 如果是可迭代对象，转换为列表并取第一个
                result_list = list(result)  # type: ignore
                document = result_list[0] if result_list else result  # type: ignore
            else:
                document = result  # type: ignore
            
            extractions = getattr(document, 'extractions', [])
            logger.debug(f"langextract提取完成，获得 {len(extractions) if extractions else 0} 个提取项")
            return document  # type: ignore
            
        except Exception as e:
            logger.error(f"langextract分析失败: {e}")
            raise
    
    def _organize_analysis_result(
        self,
        extraction_result: lx.data.AnnotatedDocument,
        original_text: str
    ) -> Dict[str, Any]:
        """
        整理分析结果为结构化数据
        """
        organized_result = {
            "basic_norms": {
                "word_count": len(original_text),
                "paragraph_count": original_text.count('\n\n') + 1,
                "errors": [],
                "format_issues": []
            },
            "content_structure": {
                "main_ideas": [],
                "key_elements": {},
                "structure_analysis": []
            },
            "language_highlights": {
                "excellent_sentences": [],
                "rhetorical_devices": {},
                "vocabulary_highlights": [],
                "expression_techniques": []
            },
            "improvement_suggestions": {
                "content_improvements": [],
                "language_improvements": [],
                "structure_improvements": [],
                "priority_issues": []
            },
            "metadata": {
                "total_extractions": len(getattr(extraction_result, 'extractions', [])),
                "analysis_timestamp": (
                    getattr(extraction_result, 'created_at', None).isoformat()  # type: ignore
                    if hasattr(extraction_result, 'created_at') and 
                       getattr(extraction_result, 'created_at', None) is not None 
                    else None
                ),
                "template_used": extraction_result.__class__.__name__
            }
        }
        
        # 按类别整理提取结果
        extractions = getattr(extraction_result, 'extractions', [])
        if extractions:
            for extraction in extractions:  # type: ignore
                category = extraction.extraction_class.lower()  # type: ignore
                
                if category in ["错别字", "标点错误", "语法问题"]:
                    organized_result["basic_norms"]["errors"].append({
                        "type": category,
                        "text": extraction.extraction_text,  # type: ignore
                        "position": self._get_position_info(extraction),
                        "attributes": extraction.attributes or {}  # type: ignore
                    })
                
                elif category in ["中心思想", "主题", "main_idea"]:
                    organized_result["content_structure"]["main_ideas"].append({
                        "text": extraction.extraction_text,  # type: ignore
                        "position": self._get_position_info(extraction),
                        "attributes": extraction.attributes or {}  # type: ignore
                    })
                
                elif category in ["修辞手法", "rhetorical_device"]:
                    device_type = extraction.attributes.get("rhetorical_type", "其他") if extraction.attributes else "其他"  # type: ignore
                    if device_type not in organized_result["language_highlights"]["rhetorical_devices"]:
                        organized_result["language_highlights"]["rhetorical_devices"][device_type] = []
                    
                    organized_result["language_highlights"]["rhetorical_devices"][device_type].append({
                        "text": extraction.extraction_text,  # type: ignore
                        "position": self._get_position_info(extraction),
                        "effect": extraction.attributes.get("effect", "") if extraction.attributes else ""  # type: ignore
                    })
                
                elif category in ["亮点句子", "highlight_sentence", "优美句子"]:
                    organized_result["language_highlights"]["excellent_sentences"].append({
                        "text": extraction.extraction_text,  # type: ignore
                        "position": self._get_position_info(extraction),
                        "highlight_type": extraction.attributes.get("highlight_type", "") if extraction.attributes else "",  # type: ignore
                        "reason": extraction.attributes.get("reason", "") if extraction.attributes else ""  # type: ignore
                    })
                
                elif category in ["改进建议", "improvement", "问题"]:
                    organized_result["improvement_suggestions"]["content_improvements"].append({
                        "issue": extraction.extraction_text,  # type: ignore
                        "position": self._get_position_info(extraction),
                        "suggestion": extraction.attributes.get("suggestion", "") if extraction.attributes else "",  # type: ignore
                        "priority": extraction.attributes.get("priority", "medium") if extraction.attributes else "medium"  # type: ignore
                    })
        
        return organized_result
    
    def _get_position_info(self, extraction: lx.data.Extraction) -> Dict[str, Any]:
        """获取提取项的位置信息"""
        if hasattr(extraction, 'char_interval') and extraction.char_interval:
            return {
                "start": extraction.char_interval.start_pos,
                "end": extraction.char_interval.end_pos,
                "has_position": True
            }
        return {"has_position": False}
    
    def _get_fallback_analysis(self, text: str) -> Dict[str, Any]:
        """获取备用分析结果（当langextract失败时）"""
        logger.warning("使用备用分析方法")
        
        return {
            "basic_norms": {
                "word_count": len(text),
                "paragraph_count": text.count('\n\n') + 1,
                "errors": [],
                "format_issues": []
            },
            "content_structure": {
                "main_ideas": [{"text": "需要进一步分析", "position": {"has_position": False}}],
                "key_elements": {},
                "structure_analysis": []
            },
            "language_highlights": {
                "excellent_sentences": [],
                "rhetorical_devices": {},
                "vocabulary_highlights": [],
                "expression_techniques": []
            },
            "improvement_suggestions": {
                "content_improvements": [],
                "language_improvements": [],
                "structure_improvements": [],
                "priority_issues": []
            },
            "metadata": {
                "total_extractions": 0,
                "analysis_timestamp": None,
                "template_used": "fallback",
                "note": "使用备用分析方法，建议检查langextract配置"
            }
        }
    
    async def generate_visualization(
        self,
        analysis_result: Dict[str, Any],
        original_text: str,
        output_path: str = "essay_analysis_visualization.html"
    ) -> str:
        """
        生成langextract可视化
        
        Args:
            analysis_result: 分析结果
            original_text: 原文
            output_path: 输出文件路径
            
        Returns:
            生成的HTML文件路径
        """
        try:
            # 重构为langextract格式的数据
            extractions = []
            
            # 添加亮点句子
            for sentence in analysis_result["language_highlights"]["excellent_sentences"]:
                extractions.append(lx.data.Extraction(
                    extraction_class="亮点句子",
                    extraction_text=sentence["text"],
                    attributes={"type": sentence.get("highlight_type", "")}
                ))
            
            # 添加修辞手法
            for device_type, devices in analysis_result["language_highlights"]["rhetorical_devices"].items():
                for device in devices:
                    extractions.append(lx.data.Extraction(
                        extraction_class="修辞手法",
                        extraction_text=device["text"],
                        attributes={"rhetorical_type": device_type, "effect": device.get("effect", "")}
                    ))
            
            # 创建AnnotatedDocument
            document = lx.data.AnnotatedDocument(
                text=original_text,
                extractions=extractions
            )
            
            # 保存为JSONL格式
            jsonl_path = output_path.replace('.html', '.jsonl')
            lx.io.save_annotated_documents(iter([document]), output_name=jsonl_path.split('.')[0], output_dir=".")
            
            # 生成可视化
            html_content = lx.visualize(jsonl_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"可视化文件已生成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成可视化失败: {e}")
            return ""
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """
        获取分析摘要
        """
        highlights_count = len(analysis_result["language_highlights"]["excellent_sentences"])
        rhetorical_count = sum(len(devices) for devices in analysis_result["language_highlights"]["rhetorical_devices"].values())
        issues_count = len(analysis_result["improvement_suggestions"]["content_improvements"])
        
        summary = f"""
📊 **分析摘要**
- 字数: {analysis_result['basic_norms']['word_count']}字
- 段落数: {analysis_result['basic_norms']['paragraph_count']}段
- 发现亮点: {highlights_count}处
- 修辞手法: {rhetorical_count}处
- 改进建议: {issues_count}条
        """
        
        return summary.strip()


# =================== 模块导出函数 ===================

def get_text_analyst_config() -> dict:
    """
    获取文本分析师配置
    
    返回OxyGent ChatAgent所需的配置参数
    """
    return {
        "name": "text_analyst",
        "desc": "严谨的文本分析专家，使用langextract进行深度结构化分析",
        "llm_model": "default_llm",
        "prompt": SYSTEM_PROMPT,
        "func_process_input": process_analysis_input
    }


# =================== 示例用法 ===================

if __name__ == "__main__":
    # 示例：创建和测试文本分析师
    helper = TextAnalystHelper()
    
    # 测试作文
    test_essay = """
    春天的公园里，樱花盛开，粉红色的花瓣如雪花般飘洒。
    微风轻拂，带来阵阵花香，沁人心脾。
    小鸟在枝头欢快地歌唱，清脆悦耳。
    孩子们在草地上嬉戏，欢声笑语回荡在空中。
    """
    
    # 清理测试文本
    test_essay = test_essay.strip().replace("\n    ", "\n")
    
    # 生成分析提示词
    prompt = helper.prepare_analysis_prompt(
        essay_content=test_essay,
        essay_type="descriptive",
        grade_level="grade_4"
    )
    
    print("📄 生成的分析提示词：")
    print(prompt)
    print("\n" + "="*50 + "\n")
    
    print("🎆 文本分析师配置：")
    config = get_text_analyst_config()
    for key, value in config.items():
        if key != "prompt":  # prompt太长，不完整显示
            print(f"  {key}: {value}")
        else:
            print(f"  {key}: [系统提示词]")