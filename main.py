#!/usr/bin/env python3
"""
AI作文评审小组 - 基于OxyGent的主程序入口

构建多智能体协作的作文评价系统
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from oxygent import MAS, Config, oxy
from oxygent.utils.env_utils import get_env_var

# 导入自定义模块
from oxy_agents import llm_config
from oxy_agents.instructional_designer import get_instructional_designer
from oxy_agents.text_analyst import create_text_analyst_agent
from oxy_agents.praiser import get_praiser
from oxy_agents.guide import get_guide
from oxy_agents.reporter import get_reporter
from oxy_agents.master_agent import get_master_agent

# 导入修复后的深度HttpLLM修复
from deep_fix_oxygent import apply_http_llm_payload_fix
from prompts import (
    designer_prompts,
    analyst_prompts,
    praiser_prompts,
    guide_prompts,
    reporter_prompts
)


def setup_logging():
    """设置日志配置"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.remove()
    logger.add(
        "logs/oxygent_essay_eval.log",
        rotation="1 day",
        retention="30 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
        encoding="utf-8"
    )


def load_environment():
    """加载环境变量"""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        logger.info("已加载环境变量文件: .env")
    else:
        logger.warning("未找到.env文件，请参考.env.example文件配置")
    
    # 验证必要的环境变量
    required_vars = ["DEFAULT_LLM_API_KEY", "DEFAULT_LLM_BASE_URL", "DEFAULT_LLM_MODEL_NAME"]
    missing_vars = []
    
    for var in required_vars:
        if not get_env_var(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        return False
    
    return True


# 配置OxyGent代理LLM模型
Config.set_agent_llm_model("default_llm")

# 定义OxyGent空间 - 基于原子化Oxy组件的架构
oxy_space = [
    # LLM配置 - 使用优化的HttpLLM，解决GitHub issue #3的payload问题
    oxy.HttpLLM(  # type: ignore
        name="default_llm",
        api_key=get_env_var("DEFAULT_LLM_API_KEY"),
        base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
        model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
        # 只使用简单的有效参数，避免复杂配置导致的问题
        llm_params={
            "temperature": 0.7,
            "max_tokens": 800,
            "stream": False,  # 明确禁用流式输出
        },
        semaphore=1,  # 限制并发，减少API压力
        timeout=60,   # 设置超时时间
        friendly_error_text="抱歉，系统暂时出现问题，请稍后重试。",
    ),
    
    # 使用独立文件中定义的智能体
    get_instructional_designer(),  # 教学模板设计师
    create_text_analyst_agent(),   # 文本分析师
    get_praiser(),                 # 赞美鼓励师
    get_guide(),                   # 启发引导师
    get_reporter(),                # 报告汇总师
    get_master_agent(),            # 主控智能体
]


async def main():
    """主函数 - 启动OxyGent MAS系统"""
    # 设置日志
    setup_logging()
    logger.info("=== AI作文评审小组启动 (基于OxyGent) ===")
    
    # 加载环境变量
    if not load_environment():
        logger.error("环境配置失败，程序退出")
        return
    
    # 应用修复后的深度HttpLLM payload修复（解决GitHub issue #3）
    if apply_http_llm_payload_fix():
        logger.info("🔧 已应用修复后的深度HttpLLM payload修复，解决moonshot API 400错误")
    else:
        logger.warning("⚠️ HttpLLM payload修复失败，可能仍有400错误")
    
    try:
        # 启动OxyGent多智能体系统
        async with MAS(oxy_space=oxy_space) as mas:
            logger.info("OxyGent MAS系统初始化完成")
            
            # 显示系统信息
            mas.show_banner()
            mas.show_mas_info()
            mas.show_org()
            
            # 启动Web服务，提供交互界面
            await mas.start_web_service(
                first_query="你好！我是AI作文评审小组，请提交你的作文或告诉我你的教学需求。"
            )
            
    except KeyboardInterrupt:
        logger.info("用户中断程序")
    except Exception as e:
        logger.error(f"系统运行错误: {e}")
        raise
    finally:
        logger.info("=== AI作文评审小组退出 ===")


def cli_main():
    """命令行入口函数"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")


if __name__ == "__main__":
    cli_main()