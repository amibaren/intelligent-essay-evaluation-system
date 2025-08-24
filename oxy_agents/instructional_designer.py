"""
教学模板设计师智能体

基于OxyGent ReActAgent的模板设计师，负责根据教师需求生成评价Schema
"""

from oxygent import oxy
from prompts import designer_prompts


class InstructionalDesigner:
    """教学模板设计师 - 基于ReActAgent"""
    
    @staticmethod
    def create_agent():
        """创建教学模板设计师智能体"""
        return oxy.ReActAgent(  # type: ignore
            name="instructional_designer",
            desc="经验丰富的教学顾问，根据教师需求动态生成作文评价模板",
            prompt=designer_prompts.SYSTEM_PROMPT,
            tools=[],  # 主要处理对话和模板生成
            llm_model="default_llm",
            max_react_rounds=3,
        )


# 导出智能体创建函数
def get_instructional_designer():
    """获取教学模板设计师智能体"""
    return InstructionalDesigner.create_agent()