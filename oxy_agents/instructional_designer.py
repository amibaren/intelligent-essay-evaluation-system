"""
教学模板设计师智能体

基于OxyGent ReActAgent的模板设计师，负责根据教师需求生成评价Schema
使用智能错误处理系统确保稳定性
"""

from oxygent import oxy
from prompts import designer_prompts
from utils.oxygent_error_handler import get_agent_factory


class InstructionalDesigner:
    """教学模板设计师 - 基于ReActAgent"""
    
    @staticmethod
    def create_agent():
        """创建教学模板设计师智能体"""
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        config = factory.create_react_agent_config(
            name="instructional_designer",
            desc="经验丰富的教学顾问，根据教师需求动态生成作文评价模板",
            prompt=designer_prompts.SYSTEM_PROMPT,
            tools=[],  # 主要处理对话和模板生成
            max_react_rounds=2,  # 模板设计不需要太多轮次
            retries=2,
            timeout=60,
            semaphore=1,
        )
        
        return oxy.ReActAgent(**config)  # type: ignore


# 导出智能体创建函数
def get_instructional_designer():
    """获取教学模板设计师智能体"""
    return InstructionalDesigner.create_agent()