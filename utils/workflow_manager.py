#!/usr/bin/env python3
"""
OxyGent工作流程管理器

重新设计智能体间的工作流程依赖关系
建立清晰的线性流程：Input → Template → Analysis → Report
修复MasterAgent跳过步骤的问题
"""

import asyncio
import time
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from loguru import logger

from oxygent import OxyRequest, OxyResponse, OxyState


class WorkflowStep(Enum):
    """工作流程步骤"""
    INPUT_VALIDATION = "input_validation"
    TEMPLATE_GENERATION = "template_generation"
    PARALLEL_ANALYSIS = "parallel_analysis"
    REPORT_GENERATION = "report_generation"
    OUTPUT_FORMATTING = "output_formatting"


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowContext:
    """工作流程上下文"""
    session_id: str
    request_type: str  # essay_evaluation, teaching_consultation
    input_data: Dict[str, Any]
    current_step: WorkflowStep
    step_results: Dict[WorkflowStep, Any]
    step_status: Dict[WorkflowStep, StepStatus]
    start_time: float
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "request_type": self.request_type,
            "input_data": self.input_data,
            "current_step": self.current_step.value,
            "step_results": {step.value: result for step, result in self.step_results.items()},
            "step_status": {step.value: status.value for step, status in self.step_status.items()},
            "start_time": self.start_time,
            "metadata": self.metadata
        }


class WorkflowManager:
    """工作流程管理器"""
    
    def __init__(self):
        self.active_workflows: Dict[str, WorkflowContext] = {}
        self.workflow_history: List[Dict[str, Any]] = []
        self.step_handlers: Dict[WorkflowStep, Callable] = {}
        
        # 定义标准工作流程
        self.standard_workflow = [
            WorkflowStep.INPUT_VALIDATION,
            WorkflowStep.TEMPLATE_GENERATION,
            WorkflowStep.PARALLEL_ANALYSIS,
            WorkflowStep.REPORT_GENERATION,
            WorkflowStep.OUTPUT_FORMATTING
        ]
        
        # 初始化步骤处理器
        self._setup_step_handlers()
    
    def _setup_step_handlers(self):
        """设置步骤处理器"""
        self.step_handlers = {
            WorkflowStep.INPUT_VALIDATION: self._handle_input_validation,
            WorkflowStep.TEMPLATE_GENERATION: self._handle_template_generation,
            WorkflowStep.PARALLEL_ANALYSIS: self._handle_parallel_analysis,
            WorkflowStep.REPORT_GENERATION: self._handle_report_generation,
            WorkflowStep.OUTPUT_FORMATTING: self._handle_output_formatting
        }
    
    async def start_workflow(self, 
                           session_id: str, 
                           request_type: str, 
                           input_data: Dict[str, Any]) -> WorkflowContext:
        """启动新的工作流程"""
        # 创建工作流程上下文
        context = WorkflowContext(
            session_id=session_id,
            request_type=request_type,
            input_data=input_data,
            current_step=WorkflowStep.INPUT_VALIDATION,
            step_results={},
            step_status={step: StepStatus.PENDING for step in self.standard_workflow},
            start_time=time.time(),
            metadata={}
        )
        
        self.active_workflows[session_id] = context
        logger.info(f"🚀 启动工作流程: {session_id} ({request_type})")
        
        return context
    
    async def execute_workflow(self, session_id: str) -> Dict[str, Any]:
        """执行工作流程"""
        if session_id not in self.active_workflows:
            raise ValueError(f"未找到工作流程: {session_id}")
        
        context = self.active_workflows[session_id]
        
        try:
            # 按顺序执行每个步骤
            for step in self.standard_workflow:
                if context.step_status[step] == StepStatus.COMPLETED:
                    logger.debug(f"⏭️ 跳过已完成步骤: {step.value}")
                    continue
                
                await self._execute_step(context, step)
                
                # 检查是否失败
                if context.step_status[step] == StepStatus.FAILED:
                    logger.error(f"❌ 工作流程在步骤 {step.value} 失败")
                    break
            
            # 生成最终结果
            final_result = self._generate_final_result(context)
            
            # 移动到历史记录
            self._archive_workflow(context)
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 工作流程执行失败: {session_id}: {e}")
            context.step_status[context.current_step] = StepStatus.FAILED
            raise
    
    async def _execute_step(self, context: WorkflowContext, step: WorkflowStep):
        """执行单个步骤"""
        logger.info(f"📋 执行步骤: {step.value} (会话: {context.session_id})")
        
        context.current_step = step
        context.step_status[step] = StepStatus.RUNNING
        
        try:
            # 调用对应的处理器
            handler = self.step_handlers.get(step)
            if handler:
                result = await handler(context)
                context.step_results[step] = result
                context.step_status[step] = StepStatus.COMPLETED
                logger.info(f"✅ 步骤完成: {step.value}")
            else:
                logger.warning(f"⚠️ 未找到步骤处理器: {step.value}")
                context.step_status[step] = StepStatus.SKIPPED
                
        except Exception as e:
            logger.error(f"❌ 步骤执行失败: {step.value}: {e}")
            context.step_status[step] = StepStatus.FAILED
            raise
    
    async def _handle_input_validation(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理输入验证步骤"""
        input_data = context.input_data
        
        # 验证必要字段
        required_fields = {
            'essay_evaluation': ['essay_content', 'grade_level'],
            'teaching_consultation': ['requirements']
        }
        
        required = required_fields.get(context.request_type, [])
        missing_fields = [field for field in required if field not in input_data]
        
        if missing_fields:
            raise ValueError(f"缺少必要字段: {missing_fields}")
        
        # 处理和清理输入数据
        cleaned_data = {
            'essay_content': input_data.get('essay_content', '').strip(),
            'grade_level': input_data.get('grade_level', 'grade_3'),
            'essay_type': input_data.get('essay_type', 'narrative'),
            'teaching_focus': input_data.get('teaching_focus', ''),
            'student_info': input_data.get('student_info', {}),
            'requirements': input_data.get('requirements', '')
        }
        
        # 添加元数据
        context.metadata.update({
            'word_count': len(cleaned_data['essay_content']),
            'estimated_complexity': self._estimate_complexity(cleaned_data),
            'validation_time': time.time()
        })
        
        logger.info(f"✅ 输入验证完成，字数: {context.metadata['word_count']}")
        return cleaned_data
    
    async def _handle_template_generation(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理模板生成步骤"""
        validated_data = context.step_results[WorkflowStep.INPUT_VALIDATION]
        
        # 构建对 instructional_designer 的调用
        template_request = {
            'agent_name': 'instructional_designer',
            'arguments': {
                'essay_content': validated_data['essay_content'],
                'grade_level': validated_data['grade_level'], 
                'essay_type': validated_data['essay_type'],
                'teaching_focus': validated_data['teaching_focus'],
                'query_type': context.request_type
            }
        }
        
        logger.info("📝 调用教学模板设计师...")
        
        # 这里应该调用实际的智能体
        # 为了演示，返回模拟结果
        template_result = {
            'evaluation_template': {
                'content_criteria': ['主题明确', '结构清晰', '语言流畅'],
                'language_criteria': ['词汇丰富', '句式多样', '修辞恰当'],
                'structure_criteria': ['开头吸引人', '过渡自然', '结尾有力'],
                'grade_specific_focus': validated_data['grade_level']
            },
            'template_metadata': {
                'generation_time': time.time(),
                'complexity_level': context.metadata.get('estimated_complexity', 'medium')
            }
        }
        
        logger.info("✅ 教学模板生成完成")
        return template_result
    
    async def _handle_parallel_analysis(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理并行分析步骤"""
        validated_data = context.step_results[WorkflowStep.INPUT_VALIDATION]
        template_data = context.step_results[WorkflowStep.TEMPLATE_GENERATION]
        
        # 准备并行分析任务
        analysis_tasks = [
            self._call_text_analyst(validated_data, template_data),
            self._call_praiser(validated_data),
            self._call_guide(validated_data)
        ]
        
        logger.info("🔄 开始并行分析...")
        
        # 执行并行分析
        try:
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            analysis_result = {
                'text_analysis': results[0] if not isinstance(results[0], Exception) else None,
                'praise_feedback': results[1] if not isinstance(results[1], Exception) else None,
                'guidance_suggestions': results[2] if not isinstance(results[2], Exception) else None,
                'analysis_metadata': {
                    'parallel_execution': True,
                    'completion_time': time.time(),
                    'success_count': sum(1 for r in results if not isinstance(r, Exception))
                }
            }
            
            logger.info(f"✅ 并行分析完成，成功: {analysis_result['analysis_metadata']['success_count']}/3")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ 并行分析失败: {e}")
            raise
    
    async def _handle_report_generation(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理报告生成步骤"""
        validated_data = context.step_results[WorkflowStep.INPUT_VALIDATION]
        template_data = context.step_results[WorkflowStep.TEMPLATE_GENERATION]
        analysis_data = context.step_results[WorkflowStep.PARALLEL_ANALYSIS]
        
        # 构建对 reporter 的调用
        report_request = {
            'agent_name': 'reporter',
            'arguments': {
                'essay_content': validated_data['essay_content'],
                'evaluation_template': template_data['evaluation_template'],
                'text_analysis': analysis_data['text_analysis'],
                'praise_feedback': analysis_data['praise_feedback'],
                'guidance_suggestions': analysis_data['guidance_suggestions'],
                'student_info': validated_data['student_info']
            }
        }
        
        logger.info("📊 调用报告汇总师...")
        
        # 模拟报告生成
        report_result = {
            'comprehensive_report': {
                'overall_score': 85,
                'strengths': ['主题明确', '语言生动'],
                'improvements': ['结构可以更清晰', '结尾需要加强'],
                'detailed_feedback': '这是一篇很好的作文...',
                'next_steps': ['多练习开头结尾', '增加描写细节']
            },
            'report_metadata': {
                'generation_time': time.time(),
                'template_used': template_data['evaluation_template'],
                'analysis_sources': list(analysis_data.keys())
            }
        }
        
        logger.info("✅ 综合报告生成完成")
        return report_result
    
    async def _handle_output_formatting(self, context: WorkflowContext) -> Dict[str, Any]:
        """处理输出格式化步骤"""
        report_data = context.step_results[WorkflowStep.REPORT_GENERATION]
        
        # 格式化最终输出
        formatted_output = {
            'evaluation_result': report_data['comprehensive_report'],
            'process_summary': {
                'total_time': time.time() - context.start_time,
                'steps_completed': [
                    step.value for step, status in context.step_status.items() 
                    if status == StepStatus.COMPLETED
                ],
                'workflow_type': context.request_type
            },
            'metadata': context.metadata
        }
        
        logger.info("✅ 输出格式化完成")
        return formatted_output
    
    async def _call_text_analyst(self, validated_data: Dict, template_data: Dict) -> Dict[str, Any]:
        """调用文本分析师"""
        await asyncio.sleep(0.5)  # 模拟API调用
        return {
            'analysis_type': 'text_analysis',
            'findings': ['语言表达清晰', '逻辑结构完整'],
            'technical_details': {'word_count': len(validated_data['essay_content'])}
        }
    
    async def _call_praiser(self, validated_data: Dict) -> Dict[str, Any]:
        """调用赞美鼓励师"""
        await asyncio.sleep(0.3)  # 模拟API调用
        return {
            'analysis_type': 'praise_feedback',
            'encouragements': ['用词很生动', '想象力丰富'],
            'motivation': '继续保持这种创作热情！'
        }
    
    async def _call_guide(self, validated_data: Dict) -> Dict[str, Any]:
        """调用启发引导师"""
        await asyncio.sleep(0.4)  # 模拟API调用
        return {
            'analysis_type': 'guidance_suggestions',
            'questions': ['可以添加更多细节描写吗？', '结尾有什么想法？'],
            'suggestions': ['尝试使用比喻句', '考虑添加人物对话']
        }
    
    def _estimate_complexity(self, data: Dict[str, Any]) -> str:
        """估算任务复杂度"""
        essay_length = len(data.get('essay_content', ''))
        
        if essay_length < 200:
            return 'low'
        elif essay_length < 500:
            return 'medium'
        else:
            return 'high'
    
    def _generate_final_result(self, context: WorkflowContext) -> Dict[str, Any]:
        """生成最终结果"""
        if WorkflowStep.OUTPUT_FORMATTING in context.step_results:
            return context.step_results[WorkflowStep.OUTPUT_FORMATTING]
        
        # 如果格式化步骤失败，返回基础结果
        return {
            'session_id': context.session_id,
            'status': 'partial_completion',
            'completed_steps': [
                step.value for step, status in context.step_status.items()
                if status == StepStatus.COMPLETED
            ],
            'available_results': {
                step.value: result for step, result in context.step_results.items()
            }
        }
    
    def _archive_workflow(self, context: WorkflowContext):
        """归档工作流程"""
        # 移动到历史记录
        self.workflow_history.append(context.to_dict())
        
        # 从活跃工作流程中移除
        if context.session_id in self.active_workflows:
            del self.active_workflows[context.session_id]
        
        # 保留最近100个历史记录
        if len(self.workflow_history) > 100:
            self.workflow_history = self.workflow_history[-100:]
        
        logger.info(f"📁 工作流程已归档: {context.session_id}")
    
    def get_workflow_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流程状态"""
        if session_id in self.active_workflows:
            context = self.active_workflows[session_id]
            return {
                'session_id': session_id,
                'current_step': context.current_step.value,
                'progress': self._calculate_progress(context),
                'step_status': {step.value: status.value for step, status in context.step_status.items()},
                'elapsed_time': time.time() - context.start_time
            }
        return None
    
    def _calculate_progress(self, context: WorkflowContext) -> float:
        """计算进度百分比"""
        completed = sum(1 for status in context.step_status.values() if status == StepStatus.COMPLETED)
        total = len(self.standard_workflow)
        return (completed / total) * 100
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        return {
            'active_workflows': len(self.active_workflows),
            'completed_workflows': len(self.workflow_history),
            'step_handlers': len(self.step_handlers),
            'standard_workflow_steps': [step.value for step in self.standard_workflow]
        }


# 全局工作流程管理器实例
workflow_manager = WorkflowManager()


def get_workflow_manager() -> WorkflowManager:
    """获取全局工作流程管理器"""
    return workflow_manager


async def execute_essay_evaluation_workflow(session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行作文评价工作流程"""
    wm = get_workflow_manager()
    
    # 启动工作流程
    context = await wm.start_workflow(session_id, 'essay_evaluation', input_data)
    
    # 执行工作流程
    result = await wm.execute_workflow(session_id)
    
    return result


async def execute_teaching_consultation_workflow(session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """执行教学咨询工作流程"""
    wm = get_workflow_manager()
    
    # 启动工作流程  
    context = await wm.start_workflow(session_id, 'teaching_consultation', input_data)
    
    # 执行工作流程
    result = await wm.execute_workflow(session_id)
    
    return result


if __name__ == "__main__":
    # 测试工作流程管理器
    print("🧪 测试工作流程管理器")
    
    async def test_workflow():
        wm = get_workflow_manager()
        
        # 测试作文评价工作流程
        test_input = {
            'essay_content': '春天来了，花开了，鸟儿在唱歌。我喜欢春天的美丽景色。',
            'grade_level': 'grade_3',
            'essay_type': 'descriptive',
            'student_info': {'name': '小明', 'age': 9}
        }
        
        session_id = f"test_session_{int(time.time())}"
        
        print(f"\n📋 开始测试工作流程: {session_id}")
        
        try:
            result = await execute_essay_evaluation_workflow(session_id, test_input)
            print(f"✅ 工作流程完成")
            print(f"结果摘要: {result.get('process_summary', {})}")
            
            # 显示系统统计
            stats = wm.get_system_stats()
            print(f"系统统计: {stats}")
            
        except Exception as e:
            print(f"❌ 工作流程失败: {e}")
    
    # 运行测试
    asyncio.run(test_workflow())
    print("\n✅ 工作流程管理器测试完成")