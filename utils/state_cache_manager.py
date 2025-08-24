#!/usr/bin/env python3
"""
OxyGent状态管理和缓存系统

解决智能体间状态污染问题，实现智能缓存和断点续传
基于OxyGent框架的最佳实践
"""

import asyncio
import json
import hashlib
import time
import pickle
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from functools import wraps
from loguru import logger

from oxygent import OxyRequest, OxyResponse, OxyState


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    timestamp: float
    ttl: float  # 生存时间（秒）
    agent_name: str
    request_hash: str
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > (self.timestamp + self.ttl)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class WorkflowState:
    """工作流状态"""
    session_id: str
    step: str
    completed_steps: List[str]
    intermediate_results: Dict[str, Any]
    timestamp: float
    message_history: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class StateManager:
    """状态管理器"""
    
    def __init__(self, max_history_size: int = 10, cache_dir: str = "cache"):
        self.max_history_size = max_history_size
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.workflow_states: Dict[str, WorkflowState] = {}
        self.message_histories: Dict[str, List[Dict[str, Any]]] = {}
        
    def clean_message_history(self, session_id: str, keep_last: int = 3) -> None:
        """清理消息历史，避免状态污染
        
        Args:
            session_id: 会话ID
            keep_last: 保留最后几条消息
        """
        if session_id in self.message_histories:
            history = self.message_histories[session_id]
            if len(history) > keep_last:
                # 保留系统消息和最后几条消息
                system_messages = [msg for msg in history if msg.get('role') == 'system']
                recent_messages = history[-keep_last:]
                
                # 去重并合并
                cleaned_history = system_messages.copy()
                for msg in recent_messages:
                    if msg not in cleaned_history:
                        cleaned_history.append(msg)
                
                self.message_histories[session_id] = cleaned_history
                logger.info(f"✅ 清理会话 {session_id} 消息历史：{len(history)} -> {len(cleaned_history)}")
    
    def add_message(self, session_id: str, message: Dict[str, Any]) -> None:
        """添加消息到历史"""
        if session_id not in self.message_histories:
            self.message_histories[session_id] = []
        
        self.message_histories[session_id].append(message)
        
        # 自动清理过长的历史
        if len(self.message_histories[session_id]) > self.max_history_size:
            self.clean_message_history(session_id)
    
    def get_message_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取消息历史"""
        return self.message_histories.get(session_id, [])
    
    def clear_session(self, session_id: str) -> None:
        """清理会话状态"""
        if session_id in self.workflow_states:
            del self.workflow_states[session_id]
        if session_id in self.message_histories:
            del self.message_histories[session_id]
        logger.info(f"✅ 清理会话状态: {session_id}")
    
    def save_workflow_state(self, session_id: str, step: str, result: Any) -> None:
        """保存工作流状态（断点续传）"""
        if session_id not in self.workflow_states:
            self.workflow_states[session_id] = WorkflowState(
                session_id=session_id,
                step=step,
                completed_steps=[],
                intermediate_results={},
                timestamp=time.time(),
                message_history=self.get_message_history(session_id)
            )
        
        state = self.workflow_states[session_id]
        state.step = step
        if step not in state.completed_steps:
            state.completed_steps.append(step)
        state.intermediate_results[step] = result
        state.timestamp = time.time()
        
        # 持久化到文件
        self._save_state_to_file(session_id, state)
        logger.info(f"✅ 保存工作流状态: {session_id} -> {step}")
    
    def load_workflow_state(self, session_id: str) -> Optional[WorkflowState]:
        """加载工作流状态"""
        if session_id in self.workflow_states:
            return self.workflow_states[session_id]
        
        # 从文件加载
        return self._load_state_from_file(session_id)
    
    def can_resume_from(self, session_id: str, step: str) -> bool:
        """检查是否可以从某步骤恢复"""
        state = self.load_workflow_state(session_id)
        if not state:
            return False
        return step in state.completed_steps
    
    def get_intermediate_result(self, session_id: str, step: str) -> Optional[Any]:
        """获取中间结果"""
        state = self.load_workflow_state(session_id)
        if not state:
            return None
        return state.intermediate_results.get(step)
    
    def _save_state_to_file(self, session_id: str, state: WorkflowState) -> None:
        """保存状态到文件"""
        try:
            state_file = self.cache_dir / f"state_{session_id}.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存状态文件失败: {e}")
    
    def _load_state_from_file(self, session_id: str) -> Optional[WorkflowState]:
        """从文件加载状态"""
        try:
            state_file = self.cache_dir / f"state_{session_id}.json"
            if not state_file.exists():
                return None
            
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = WorkflowState(**data)
            self.workflow_states[session_id] = state
            return state
            
        except Exception as e:
            logger.error(f"❌ 加载状态文件失败: {e}")
            return None


class IntelligentCache:
    """智能缓存系统"""
    
    def __init__(self, cache_dir: str = "cache", default_ttl: float = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_cache_key(self, 
                          agent_name: str, 
                          oxy_request: OxyRequest,
                          extra_params: Optional[Dict] = None) -> str:
        """生成缓存键"""
        # 基于请求内容和参数生成hash
        content_data = {
            "query": oxy_request.get_query(),
            "arguments": oxy_request.arguments if hasattr(oxy_request, 'arguments') else {},
            "agent_name": agent_name,
            "extra_params": extra_params or {}
        }
        
        content_str = json.dumps(content_data, sort_keys=True, ensure_ascii=False)
        cache_key = hashlib.md5(content_str.encode()).hexdigest()
        return f"{agent_name}_{cache_key}"
    
    def get(self, agent_name: str, oxy_request: OxyRequest, 
            extra_params: Optional[Dict] = None) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = self._generate_cache_key(agent_name, oxy_request, extra_params)
        
        # 先检查内存缓存
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if not entry.is_expired():
                self.hit_count += 1
                logger.info(f"🎯 缓存命中: {agent_name} ({cache_key[:8]}...)")
                return entry.data
            else:
                # 过期则删除
                del self.memory_cache[cache_key]
        
        # 检查磁盘缓存
        cached_data = self._load_from_disk(cache_key)
        if cached_data:
            self.hit_count += 1
            logger.info(f"🎯 磁盘缓存命中: {agent_name} ({cache_key[:8]}...)")
            return cached_data
        
        self.miss_count += 1
        logger.debug(f"❌ 缓存未命中: {agent_name} ({cache_key[:8]}...)")
        return None
    
    def set(self, agent_name: str, oxy_request: OxyRequest, 
            result: Any, ttl: Optional[float] = None,
            extra_params: Optional[Dict] = None) -> None:
        """设置缓存"""
        cache_key = self._generate_cache_key(agent_name, oxy_request, extra_params)
        ttl = ttl or self.default_ttl
        
        # 生成请求hash用于验证
        request_hash = hashlib.md5(
            str(oxy_request.get_query()).encode()
        ).hexdigest()
        
        entry = CacheEntry(
            key=cache_key,
            data=result,
            timestamp=time.time(),
            ttl=ttl,
            agent_name=agent_name,
            request_hash=request_hash
        )
        
        # 保存到内存和磁盘
        self.memory_cache[cache_key] = entry
        self._save_to_disk(cache_key, entry)
        
        logger.info(f"💾 缓存保存: {agent_name} ({cache_key[:8]}...) TTL={ttl}s")
    
    def _save_to_disk(self, cache_key: str, entry: CacheEntry) -> None:
        """保存到磁盘"""
        try:
            cache_file = self.cache_dir / f"cache_{cache_key}.pkl"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except Exception as e:
            logger.error(f"❌ 保存缓存文件失败: {e}")
    
    def _load_from_disk(self, cache_key: str) -> Optional[Any]:
        """从磁盘加载"""
        try:
            cache_file = self.cache_dir / f"cache_{cache_key}.pkl"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                entry: CacheEntry = pickle.load(f)
            
            if entry.is_expired():
                cache_file.unlink()  # 删除过期文件
                return None
            
            # 加载到内存缓存
            self.memory_cache[cache_key] = entry
            return entry.data
            
        except Exception as e:
            logger.error(f"❌ 加载缓存文件失败: {e}")
            return None
    
    def clear_expired(self) -> int:
        """清理过期缓存"""
        cleared_count = 0
        
        # 清理内存缓存
        expired_keys = [key for key, entry in self.memory_cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self.memory_cache[key]
            cleared_count += 1
        
        # 清理磁盘缓存
        for cache_file in self.cache_dir.glob("cache_*.pkl"):
            try:
                with open(cache_file, 'rb') as f:
                    entry: CacheEntry = pickle.load(f)
                if entry.is_expired():
                    cache_file.unlink()
                    cleared_count += 1
            except Exception:
                # 如果文件损坏，也删除
                cache_file.unlink()
                cleared_count += 1
        
        if cleared_count > 0:
            logger.info(f"🧹 清理过期缓存: {cleared_count} 个条目")
        
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": f"{hit_rate:.1f}%",
            "memory_cache_size": len(self.memory_cache),
            "disk_cache_files": len(list(self.cache_dir.glob("cache_*.pkl")))
        }


class CacheableAgentWrapper:
    """可缓存的智能体包装器"""
    
    def __init__(self, agent, cache: IntelligentCache, cache_ttl: float = 1800):
        self.agent = agent
        self.cache = cache
        self.cache_ttl = cache_ttl
        self.agent_name = getattr(agent, 'name', 'unknown_agent')
    
    async def execute(self, oxy_request: OxyRequest) -> OxyResponse:
        """执行智能体调用（带缓存）"""
        # 尝试从缓存获取
        cached_result = self.cache.get(self.agent_name, oxy_request)
        if cached_result:
            return cached_result
        
        # 执行实际调用
        start_time = time.time()
        result = await self.agent.chat(oxy_request)
        execution_time = time.time() - start_time
        
        # 只缓存成功的结果
        if result.state == OxyState.COMPLETED:
            self.cache.set(
                self.agent_name, 
                oxy_request, 
                result, 
                self.cache_ttl
            )
            logger.info(f"✅ 智能体执行完成并缓存: {self.agent_name} ({execution_time:.2f}s)")
        else:
            logger.warning(f"⚠️ 智能体执行失败，不缓存: {self.agent_name}")
        
        return result


# 全局实例
state_manager = StateManager()
intelligent_cache = IntelligentCache()


def with_state_management(session_id_key: str = "session_id"):
    """状态管理装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 提取session_id
            session_id = kwargs.get(session_id_key, "default_session")
            
            try:
                # 执行前清理消息历史
                state_manager.clean_message_history(session_id)
                
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 保存结果状态
                step_name = func.__name__
                state_manager.save_workflow_state(session_id, step_name, result)
                
                return result
                
            except Exception as e:
                logger.error(f"❌ 状态管理执行失败: {e}")
                raise
                
        return wrapper
    return decorator


def with_intelligent_cache(cache_ttl: float = 1800):
    """智能缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 这里可以根据函数参数生成缓存键
            # 具体实现取决于函数签名
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def get_state_manager() -> StateManager:
    """获取全局状态管理器"""
    return state_manager


def get_intelligent_cache() -> IntelligentCache:
    """获取全局智能缓存"""
    return intelligent_cache


def create_cacheable_agent(agent, cache_ttl: float = 1800) -> CacheableAgentWrapper:
    """创建可缓存的智能体包装器"""
    return CacheableAgentWrapper(agent, intelligent_cache, cache_ttl)


if __name__ == "__main__":
    # 测试状态管理和缓存系统
    print("🧪 测试状态管理和缓存系统")
    
    # 测试状态管理
    print("\n📊 测试状态管理")
    sm = StateManager()
    
    session_id = "test_session_001"
    sm.add_message(session_id, {"role": "user", "content": "测试消息1"})
    sm.add_message(session_id, {"role": "assistant", "content": "回复1"})
    sm.save_workflow_state(session_id, "step1", {"result": "完成步骤1"})
    
    print(f"消息历史: {len(sm.get_message_history(session_id))} 条")
    print(f"可以从step1恢复: {sm.can_resume_from(session_id, 'step1')}")
    print(f"中间结果: {sm.get_intermediate_result(session_id, 'step1')}")
    
    # 测试缓存
    print("\n💾 测试智能缓存")
    cache = IntelligentCache()
    
    # 模拟缓存操作
    class MockRequest:
        def __init__(self, query):
            self.query = query
            self.arguments = {}
        def get_query(self):
            return self.query
    
    request1 = MockRequest("测试请求1")
    
    # 第一次访问（未命中）
    # 注意：这里的MockRequest只用于测试，实际使用中应传入真正的OxyRequest对象
    try:
        result1 = cache.get("test_agent", request1)
        print(f"第一次访问: {result1}")
        
        # 设置缓存
        cache.set("test_agent", request1, "测试结果1", ttl=60)
        
        # 第二次访问（命中）
        result2 = cache.get("test_agent", request1)
        print(f"第二次访问: {result2}")
        
    except Exception as e:
        print(f"缓存测试过程中出现问题: {e}")
    
    # 统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
    
    print("\n✅ 状态管理和缓存系统测试完成")