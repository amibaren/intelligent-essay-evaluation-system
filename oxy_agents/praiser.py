"""
赞美鼓励师智能体

基于OxyGent ChatAgent的赞美鼓励师，专注发现和表扬学生作文亮点
"""

from oxygent import oxy
from prompts import praiser_prompts


class Praiser:
    """赞美鼓励师 - 基于ChatAgent"""
    
    @staticmethod
    def create_agent():
        """创建赞美鼓励师智能体"""
        return oxy.ChatAgent(  # type: ignore
            name="praiser",
            desc="热情阳光的AI老师，善于发现学生作文的亮点并给予鼓励",
            prompt=praiser_prompts.SYSTEM_PROMPT,
        )


# 导出智能体创建函数
def get_praiser():
    """获取赞美鼓励师智能体"""
    return Praiser.create_agent()