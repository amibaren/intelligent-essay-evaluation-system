"""
报告汇总师智能体

基于OxyGent ReActAgent的报告汇总师，优化并行调用多个分析师生成最终报告
使用智能错误处理系统确保稳定性
"""

from oxygent import oxy
from prompts import reporter_prompts
from utils.oxygent_error_handler import get_agent_factory


class Reporter:
    """报告汇总师 - 基于ReActAgent，优化并行处理"""
    
    @staticmethod
    def create_agent():
        """创建报告汇总师智能体
        
        使用OxyGent框架的子智能体机制，让框架处理并行调用和错误重试
        """
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        config = factory.create_react_agent_config(
            name="reporter",
            desc="专业的报告撰写员，整合多个分析师的评价生成综合报告",
            prompt=reporter_prompts.SYSTEM_PROMPT,
            sub_agents=["text_analyst", "praiser", "guide"],
            max_react_rounds=2,  # 限制ReAct轮数，避免无限循环
            retries=2,           # 最多重试2次
            timeout=180,         # 180秒超时（需要协调多个子智能体）
            semaphore=1,         # 限制并发数量
        )
        
        return oxy.ReActAgent(**config)  # type: ignore


# 导出智能体创建函数
def get_reporter():
    """获取报告汇总师智能体"""
    return Reporter.create_agent()