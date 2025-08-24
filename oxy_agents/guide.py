"""
启发引导师智能体

基于OxyGent ChatAgent的引导师，通过提问启发学生思考
使用智能错误处理系统确保稳定性
"""

from oxygent import oxy
from prompts import guide_prompts
from utils.oxygent_error_handler import get_agent_factory


class Guide:
    """启发引导师 - 基于ChatAgent"""
    
    @staticmethod
    def create_agent():
        """创建启发引导师智能体"""
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        config = factory.create_chat_agent_config(
            name="guide",
            desc="温和的引导老师，通过提问启发学生发现问题并思考改进",
            prompt=guide_prompts.SYSTEM_PROMPT,
            retries=2,           # 最多重试2次
            timeout=60,          # 60秒超时
            semaphore=1,         # 限制并发数量
        )
        
        return oxy.ChatAgent(**config)  # type: ignore


# 导出智能体创建函数
def get_guide():
    """获取启发引导师智能体"""
    return Guide.create_agent()