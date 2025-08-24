"""
启发引导师智能体

基于OxyGent ChatAgent的引导师，通过提问启发学生思考
"""

from oxygent import oxy
from prompts import guide_prompts


class Guide:
    """启发引导师 - 基于ChatAgent"""
    
    @staticmethod
    def create_agent():
        """创建启发引导师智能体"""
        return oxy.ChatAgent(  # type: ignore
            name="guide",
            desc="温和的引导老师，通过提问启发学生发现问题并思考改进",
            prompt=guide_prompts.SYSTEM_PROMPT,
        )


# 导出智能体创建函数
def get_guide():
    """获取启发引导师智能体"""
    return Guide.create_agent()