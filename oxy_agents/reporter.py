"""
报告汇总师智能体

基于OxyGent ReActAgent的报告汇总师，整合所有评价生成最终报告
"""

from oxygent import oxy
from prompts import reporter_prompts


class Reporter:
    """报告汇总师 - 基于ReActAgent"""
    
    @staticmethod
    def create_agent():
        """创建报告汇总师智能体"""
        return oxy.ReActAgent(  # type: ignore
            name="reporter",
            desc="专业的报告撰写员，整合所有智能体的评价生成综合报告",
            prompt=reporter_prompts.SYSTEM_PROMPT,
            sub_agents=["text_analyst", "praiser", "guide"],
            llm_model="default_llm",
            max_react_rounds=2,
        )


# 导出智能体创建函数
def get_reporter():
    """获取报告汇总师智能体"""
    return Reporter.create_agent()