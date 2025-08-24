"""
LLM配置模块

基于OxyGent HttpLLM组件的配置管理
"""

from oxygent import oxy
from oxygent.utils.env_utils import get_env_var
from loguru import logger


class LLMConfig:
    """LLM配置管理器"""
    
    @staticmethod
    def create_default_llm():
        """创建默认LLM配置"""
        return oxy.HttpLLM(  # type: ignore
            name="default_llm",
            api_key=get_env_var("DEFAULT_LLM_API_KEY"),
            base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
            model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
            llm_params={
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 0.9,
            },
            semaphore=4,
            timeout=240,
        )
    
    @staticmethod
    def create_analysis_llm():
        """创建用于文本分析的LLM配置(更严格的参数)"""
        return oxy.HttpLLM(  # type: ignore
            name="analysis_llm",
            api_key=get_env_var("DEFAULT_LLM_API_KEY"),
            base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
            model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
            llm_params={
                "temperature": 0.1,  # 更低温度，确保分析客观
                "max_tokens": 3000,
                "top_p": 0.8,
            },
            semaphore=2,
            timeout=300,
        )
    
    @staticmethod
    def create_creative_llm():
        """创建用于创意表达的LLM配置(更灵活的参数)"""
        return oxy.HttpLLM(  # type: ignore
            name="creative_llm",
            api_key=get_env_var("DEFAULT_LLM_API_KEY"),
            base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
            model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
            llm_params={
                "temperature": 0.9,  # 更高温度，增加创造性
                "max_tokens": 1500,
                "top_p": 0.95,
            },
            semaphore=3,
            timeout=180,
        )
    
    @staticmethod
    def validate_llm_config():
        """验证LLM配置是否正确"""
        required_vars = [
            "DEFAULT_LLM_API_KEY",
            "DEFAULT_LLM_BASE_URL", 
            "DEFAULT_LLM_MODEL_NAME"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not get_env_var(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"LLM配置验证失败，缺少环境变量: {missing_vars}")
            return False
        
        logger.info("LLM配置验证通过")
        return True
    
    @staticmethod
    def get_model_info():
        """获取模型信息"""
        return {
            "model_name": get_env_var("DEFAULT_LLM_MODEL_NAME"),
            "base_url": get_env_var("DEFAULT_LLM_BASE_URL"),
            "api_configured": bool(get_env_var("DEFAULT_LLM_API_KEY"))
        }