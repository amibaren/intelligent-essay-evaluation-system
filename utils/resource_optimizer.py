#!/usr/bin/env python3
"""
OxyGent资源优化和并行处理系统

解决智能体间伪并行导致的资源浪费问题
实现真正的异步任务队列和智能资源管理
基于OxyGent框架的最佳实践
"""

import asyncio
import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from functools import wraps
import psutil
from loguru import logger

from oxygent import OxyRequest, OxyResponse, OxyState


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ResourceUsage:
    """资源使用情况"""
    cpu_percent: float
    memory_percent: float
    active_agents: int
    queued_tasks: int
    token_usage: int
    timestamp: float


@dataclass
class TaskMetrics:
    """任务指标"""
    agent_name: str
    start_time: float
    end_time: Optional[float]
    token_consumed: int
    success: bool
    execution_time: Optional[float]


class TokenManager:
    """Token管理器 - 控制API调用消耗"""
    
    def __init__(self, max_tokens_per_minute: int = 10000, max_tokens_per_request: int = 2000):
        self.max_tokens_per_minute = max_tokens_per_minute
        self.max_tokens_per_request = max_tokens_per_request
        self.token_usage_history = deque(maxlen=60)  # 保留60秒的历史
        self.current_minute_tokens = 0
        self.last_reset_time = time.time()
        self.lock = threading.Lock()
    
    def _reset_minute_counter(self):
        """重置每分钟计数器"""
        current_time = time.time()
        if current_time - self.last_reset_time >= 60:
            self.current_minute_tokens = 0
            self.last_reset_time = current_time
    
    def can_consume_tokens(self, tokens: int) -> bool:
        """检查是否可以消耗指定数量的token"""
        with self.lock:
            self._reset_minute_counter()
            
            # 检查单次请求限制
            if tokens > self.max_tokens_per_request:
                logger.warning(f"⚠️ 单次请求token过多: {tokens} > {self.max_tokens_per_request}")
                return False
            
            # 检查每分钟限制
            if self.current_minute_tokens + tokens > self.max_tokens_per_minute:
                logger.warning(f"⚠️ 每分钟token额度不足: {self.current_minute_tokens + tokens} > {self.max_tokens_per_minute}")
                return False
            
            return True
    
    def consume_tokens(self, tokens: int) -> bool:
        """消耗token"""
        with self.lock:
            if self.can_consume_tokens(tokens):
                self.current_minute_tokens += tokens
                self.token_usage_history.append({
                    'timestamp': time.time(),
                    'tokens': tokens
                })
                logger.debug(f"💰 消耗token: {tokens}, 当前分钟总计: {self.current_minute_tokens}")
                return True
            return False
    
    def get_remaining_tokens(self) -> int:
        """获取剩余token数量"""
        with self.lock:
            self._reset_minute_counter()
            return self.max_tokens_per_minute - self.current_minute_tokens
    
    def estimate_wait_time(self, tokens: int) -> float:
        """估算需要等待的时间（秒）"""
        if self.can_consume_tokens(tokens):
            return 0.0
        
        # 简单估算：等到下一分钟开始
        current_time = time.time()
        next_minute = self.last_reset_time + 60
        return max(0, next_minute - current_time)


class AsyncTaskQueue:
    """异步任务队列 - 真正的并行处理"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.task_queue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.completed_tasks: List[TaskMetrics] = []
        self.running = False
        self.workers: List[asyncio.Task] = []
        self.task_counter = 0
        self.lock = asyncio.Lock()
    
    async def start(self):
        """启动任务队列"""
        if self.running:
            return
        
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(f"worker_{i}"))
            for i in range(self.max_workers)
        ]
        logger.info(f"✅ 启动异步任务队列，工作线程数: {self.max_workers}")
    
    async def stop(self):
        """停止任务队列"""
        self.running = False
        
        # 等待所有工作线程完成
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)
        
        # 取消活跃任务
        for task in self.active_tasks.values():
            task.cancel()
        
        logger.info("🛑 异步任务队列已停止")
    
    async def submit_task(self, 
                         agent_name: str, 
                         task_func: Callable, 
                         *args, 
                         priority: TaskPriority = TaskPriority.NORMAL,
                         **kwargs) -> str:
        """提交任务到队列"""
        task_id = f"{agent_name}_{self.task_counter}_{int(time.time())}"
        self.task_counter += 1
        
        task_item = (
            -priority.value,  # 负数用于优先队列排序
            time.time(),      # 提交时间
            task_id,
            agent_name,
            task_func,
            args,
            kwargs
        )
        
        await self.task_queue.put(task_item)
        logger.info(f"📋 提交任务: {task_id} (优先级: {priority.name})")
        return task_id
    
    async def _worker(self, worker_name: str):
        """工作线程"""
        logger.info(f"🔧 启动工作线程: {worker_name}")
        
        while self.running:
            try:
                # 等待任务，设置超时避免无限等待
                try:
                    task_item = await asyncio.wait_for(
                        self.task_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                priority, submit_time, task_id, agent_name, task_func, args, kwargs = task_item
                
                # 创建并执行任务
                async with self.lock:
                    if not self.running:
                        break
                    
                    task = asyncio.create_task(
                        self._execute_task(task_id, agent_name, task_func, *args, **kwargs)
                    )
                    self.active_tasks[task_id] = task
                
                try:
                    await task
                finally:
                    async with self.lock:
                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id]
                        self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 工作线程 {worker_name} 错误: {e}")
        
        logger.info(f"🏁 工作线程退出: {worker_name}")
    
    async def _execute_task(self, task_id: str, agent_name: str, task_func: Callable, *args, **kwargs):
        """执行具体任务"""
        start_time = time.time()
        success = False
        token_consumed = 0
        
        try:
            logger.info(f"🚀 开始执行任务: {task_id}")
            
            # 执行任务
            result = await task_func(*args, **kwargs)
            
            # 尝试获取token消耗信息
            if hasattr(result, 'token_usage'):
                token_consumed = result.token_usage
            elif isinstance(result, dict) and 'token_usage' in result:
                token_consumed = result['token_usage']
            
            success = True
            logger.info(f"✅ 任务完成: {task_id} ({time.time() - start_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"❌ 任务执行失败: {task_id}: {e}")
            raise
        finally:
            # 记录任务指标
            metrics = TaskMetrics(
                agent_name=agent_name,
                start_time=start_time,
                end_time=time.time(),
                token_consumed=token_consumed,
                success=success,
                execution_time=time.time() - start_time
            )
            self.completed_tasks.append(metrics)
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "running": self.running,
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_tasks),
            "workers": len(self.workers),
            "completed_tasks": len(self.completed_tasks)
        }


class ResourceOptimizer:
    """资源优化器"""
    
    def __init__(self, token_manager: TokenManager, task_queue: AsyncTaskQueue):
        self.token_manager = token_manager
        self.task_queue = task_queue
        self.resource_history: List[ResourceUsage] = []
        self.optimization_enabled = True
        
    def monitor_resources(self) -> ResourceUsage:
        """监控系统资源"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_percent = psutil.virtual_memory().percent
        
        usage = ResourceUsage(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            active_agents=len(self.task_queue.active_tasks),
            queued_tasks=self.task_queue.task_queue.qsize(),
            token_usage=self.token_manager.current_minute_tokens,
            timestamp=time.time()
        )
        
        self.resource_history.append(usage)
        
        # 保留最近1小时的历史
        if len(self.resource_history) > 3600:
            self.resource_history = self.resource_history[-3600:]
        
        return usage
    
    def should_throttle(self) -> bool:
        """判断是否需要限流"""
        if not self.optimization_enabled:
            return False
        
        usage = self.monitor_resources()
        
        # 检查资源使用情况
        if usage.cpu_percent > 80:
            logger.warning(f"⚠️ CPU使用率过高: {usage.cpu_percent}%")
            return True
        
        if usage.memory_percent > 85:
            logger.warning(f"⚠️ 内存使用率过高: {usage.memory_percent}%")
            return True
        
        if usage.active_agents > self.task_queue.max_workers * 1.5:
            logger.warning(f"⚠️ 活跃智能体过多: {usage.active_agents}")
            return True
        
        return False
    
    async def optimize_execution(self, agent_name: str, task_func: Callable, *args, **kwargs):
        """优化执行策略"""
        # 检查是否需要限流
        if self.should_throttle():
            await asyncio.sleep(1)  # 简单的退避策略
        
        # 估算token消耗
        estimated_tokens = self._estimate_token_usage(agent_name, args, kwargs)
        
        # 检查token额度
        if not self.token_manager.can_consume_tokens(estimated_tokens):
            wait_time = self.token_manager.estimate_wait_time(estimated_tokens)
            if wait_time > 0:
                logger.info(f"⏳ Token额度不足，等待 {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # 选择执行策略
        if self._should_use_queue(agent_name):
            # 使用任务队列
            priority = self._get_task_priority(agent_name)
            task_id = await self.task_queue.submit_task(
                agent_name, task_func, *args, priority=priority, **kwargs
            )
            return task_id
        else:
            # 直接执行
            return await task_func(*args, **kwargs)
    
    def _estimate_token_usage(self, agent_name: str, args: tuple, kwargs: dict) -> int:
        """估算token使用量"""
        # 基于历史数据估算
        base_tokens = 200  # 基础token数
        
        # 根据输入内容估算
        total_chars = 0
        for arg in args:
            if isinstance(arg, str):
                total_chars += len(arg)
            elif hasattr(arg, 'get_query'):
                total_chars += len(str(arg.get_query()))
        
        for value in kwargs.values():
            if isinstance(value, str):
                total_chars += len(value)
        
        # 简单的字符到token转换（中文约1.5字符=1token）
        estimated_tokens = base_tokens + (total_chars // 2)
        
        # 不同智能体的调整系数
        multipliers = {
            'text_analyst': 1.5,  # 文本分析消耗更多
            'reporter': 1.3,      # 报告生成需要更多
            'master_agent': 1.2,  # 主控智能体需要协调
            'instructional_designer': 1.1,
            'praiser': 0.8,       # 赞美师消耗较少
            'guide': 0.9          # 引导师消耗较少
        }
        
        multiplier = multipliers.get(agent_name, 1.0)
        return int(estimated_tokens * multiplier)
    
    def _should_use_queue(self, agent_name: str) -> bool:
        """判断是否应该使用任务队列"""
        # 对于复杂的智能体使用队列
        queue_agents = {'text_analyst', 'reporter', 'master_agent'}
        return agent_name in queue_agents
    
    def _get_task_priority(self, agent_name: str) -> TaskPriority:
        """获取任务优先级"""
        priorities = {
            'master_agent': TaskPriority.URGENT,
            'instructional_designer': TaskPriority.HIGH,
            'reporter': TaskPriority.HIGH,
            'text_analyst': TaskPriority.NORMAL,
            'praiser': TaskPriority.LOW,
            'guide': TaskPriority.LOW
        }
        return priorities.get(agent_name, TaskPriority.NORMAL)
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        if not self.resource_history:
            return {"message": "暂无数据"}
        
        recent_usage = self.resource_history[-10:] if self.resource_history else []
        avg_cpu = sum(u.cpu_percent for u in recent_usage) / len(recent_usage)
        avg_memory = sum(u.memory_percent for u in recent_usage) / len(recent_usage)
        
        return {
            "optimization_enabled": self.optimization_enabled,
            "avg_cpu_percent": f"{avg_cpu:.1f}%",
            "avg_memory_percent": f"{avg_memory:.1f}%",
            "token_remaining": self.token_manager.get_remaining_tokens(),
            "queue_status": self.task_queue.get_queue_status(),
            "resource_samples": len(self.resource_history)
        }


def with_resource_optimization(optimizer: ResourceOptimizer):
    """资源优化装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            agent_name = getattr(func, '__name__', 'unknown')
            return await optimizer.optimize_execution(agent_name, func, *args, **kwargs)
        return wrapper
    return decorator


# 全局实例
token_manager = TokenManager()
task_queue = AsyncTaskQueue(max_workers=3)
resource_optimizer = ResourceOptimizer(token_manager, task_queue)


async def initialize_resource_system():
    """初始化资源管理系统"""
    await task_queue.start()
    logger.info("🚀 资源优化系统启动完成")


async def cleanup_resource_system():
    """清理资源管理系统"""
    await task_queue.stop()
    logger.info("🏁 资源优化系统清理完成")


def get_token_manager() -> TokenManager:
    """获取全局Token管理器"""
    return token_manager


def get_task_queue() -> AsyncTaskQueue:
    """获取全局任务队列"""
    return task_queue


def get_resource_optimizer() -> ResourceOptimizer:
    """获取全局资源优化器"""
    return resource_optimizer


if __name__ == "__main__":
    # 测试资源优化系统
    print("🧪 测试资源优化系统")
    
    async def test_system():
        # 初始化
        await initialize_resource_system()
        
        # 测试Token管理
        print("\n💰 测试Token管理")
        tm = get_token_manager()
        print(f"可消耗500 tokens: {tm.can_consume_tokens(500)}")
        print(f"消耗300 tokens: {tm.consume_tokens(300)}")
        print(f"剩余tokens: {tm.get_remaining_tokens()}")
        
        # 测试任务队列
        print("\n📋 测试任务队列")
        tq = get_task_queue()
        
        async def test_task(name: str, delay: float = 1.0):
            await asyncio.sleep(delay)
            return f"任务 {name} 完成"
        
        # 提交几个测试任务
        task_ids = []
        for i in range(3):
            task_id = await tq.submit_task(
                f"test_agent_{i}", 
                test_task, 
                f"task_{i}", 
                0.5,
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # 等待一段时间
        await asyncio.sleep(2)
        
        # 获取状态
        status = tq.get_queue_status()
        print(f"队列状态: {status}")
        
        # 测试资源优化器
        print("\n📊 测试资源优化器")
        ro = get_resource_optimizer()
        stats = ro.get_optimization_stats()
        print(f"优化统计: {stats}")
        
        # 清理
        await cleanup_resource_system()
    
    # 运行测试
    asyncio.run(test_system())
    print("\n✅ 资源优化系统测试完成")