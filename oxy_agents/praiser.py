"""
赞美鼓励师智能体

基于OxyGent ChatAgent的赞美鼓励师，专注发现和表扬学生作文亮点
使用智能错误处理系统确保稳定性
"""

from oxygent import oxy
from prompts import praiser_prompts
from utils.oxygent_error_handler import get_agent_factory


class Praiser:
    """赞美鼓励师 - 基于ChatAgent"""
    
    @staticmethod
    def create_agent():
        """创建赞美鼓励师智能体"""
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        config = factory.create_chat_agent_config(
            name="praiser",
            desc="热情阳光的AI老师，善于发现学生作文的亮点并给予鼓励",
            prompt=praiser_prompts.SYSTEM_PROMPT,
            retries=2,           # 最多重试2次
            timeout=60,          # 60秒超时
            semaphore=1,         # 限制并发数量
        )
        
        return oxy.ChatAgent(**config)  # type: ignore


# 导出智能体创建函数
def get_praiser():
    """获取赞美鼓励师智能体"""
    return Praiser.create_agent()