"""
教学模板设计师智能体

基于OxyGent ChatAgent的模板设计师，负责根据教师需求生成评价Schema
使用智能错误处理系统确保稳定性
"""

from oxygent import oxy
from prompts import designer_prompts
from utils.oxygent_error_handler import get_agent_factory
from loguru import logger


class InstructionalDesigner:
    """教学模板设计师 - 基于ChatAgent"""
    
    @staticmethod
    def create_agent():
        """创建教学模板设计师智能体"""
        # 使用智能错误处理工厂创建配置
        factory = get_agent_factory()
        
        # 创建扩展版的系统提示词，包含参数处理指令
        extended_system_prompt = designer_prompts.SYSTEM_PROMPT + """

## 🎯 自动参数接收说明

当本智能体被主控智能体调用时，会自动接收以下参数，无需询问用户：

**可用参数（自动填充）：**
- essay_content: 作文完整内容
- grade_level: 学生年级（如"三年级"）
- essay_type: 作文类型（如"记叙文"）
- teaching_focus: 教学重点（如"语言表达"）
- additional_requirements: 额外要求

**处理规则：**
1. **直接使用参数**：收到调用时立即使用上述参数生成模板
2. **智能推断**：如果参数缺失，根据作文内容推断年级和类型
3. **避免询问**：绝不向用户重复询问已提供的信息
4. **立即响应**：收到参数后2秒内生成完整模板

**使用示例：**
收到调用参数：
```
essay_content="我的妈妈很温柔..."
grade_level="三年级"
essay_type="记叙文"
```

立即生成模板，无需询问。
"""
        
        config = factory.create_chat_agent_config(
            name="instructional_designer",
            desc="经验丰富的教学顾问，根据教师需求动态生成作文评价模板",
            prompt=extended_system_prompt,
            retries=3,  # 保留重试次数
            timeout=120,  # 保留超时时间
            semaphore=1,
        )
        
        agent = oxy.ChatAgent(**config)  # type: ignore
        logger.info(f"✅ 教学模板设计师智能体已创建，确保作为子智能体可被访问")
        return agent


# 导出智能体创建函数
def get_instructional_designer():
    """获取教学模板设计师智能体"""
    return InstructionalDesigner.create_agent()