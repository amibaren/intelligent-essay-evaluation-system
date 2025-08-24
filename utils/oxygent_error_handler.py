#!/usr/bin/env python3
"""
OxyGent智能错误处理中心

整合OxyGent框架内置的错误处理能力与自定义错误处理逻辑
提供统一的错误处理、重试机制和状态管理
基于OxyGent官方文档的最佳实践
"""

import asyncio
import time
import traceback
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
from loguru import logger

from oxygent import OxyRequest, OxyResponse, OxyState
from utils.performance import ErrorHandler, PerformanceMonitor


class OxyGentErrorHandler:
    """OxyGent智能错误处理器"""
    
    def __init__(self, performance_monitor: Optional[PerformanceMonitor] = None):
        self.error_handler = ErrorHandler()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.circuit_breaker_state = {}  # 熔断器状态
        
    def create_oxygent_config(self, 
                            agent_name: str,
                            max_retries: int = 2,
                            timeout: int = 60,
                            semaphore: int = 1,
                            circuit_breaker_threshold: int = 5) -> Dict[str, Any]:
        """创建符合OxyGent最佳实践的配置
        
        Args:
            agent_name: 智能体名称
            max_retries: 最大重试次数（OxyGent内置）
            timeout: 超时时间（OxyGent内置）
            semaphore: 并发控制（OxyGent内置）
            circuit_breaker_threshold: 熔断器阈值
            
        Returns:
            OxyGent配置字典
        """
        config = {
            "retries": max_retries,
            "timeout": timeout, 
            "semaphore": semaphore,
            # 为每个智能体初始化熔断器状态
            "_circuit_breaker_errors": 0,
            "_circuit_breaker_threshold": circuit_breaker_threshold,
            "_last_error_time": None
        }
        
        self.circuit_breaker_state[agent_name] = {
            "errors": 0,
            "threshold": circuit_breaker_threshold,
            "last_error_time": None,
            "is_open": False,
            "next_retry_time": None
        }
        
        logger.info(f"✅ 为智能体 {agent_name} 创建OxyGent错误处理配置: retries={max_retries}, timeout={timeout}s")
        return config
    
    def check_circuit_breaker(self, agent_name: str) -> bool:
        """检查熔断器状态
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            True如果可以继续执行，False如果被熔断
        """
        if agent_name not in self.circuit_breaker_state:
            return True
        
        state = self.circuit_breaker_state[agent_name]
        
        # 如果熔断器是开启状态
        if state["is_open"]:
            # 检查是否可以尝试恢复
            if state["next_retry_time"] and time.time() < state["next_retry_time"]:
                logger.warning(f"⚡ 智能体 {agent_name} 熔断器开启中，等待恢复...")
                return False
            else:
                # 尝试半开状态
                logger.info(f"🔄 智能体 {agent_name} 熔断器进入半开状态，尝试恢复...")
                state["is_open"] = False
                return True
        
        return True
    
    def record_error(self, agent_name: str, error: Exception) -> None:
        """记录错误并更新熔断器状态
        
        Args:
            agent_name: 智能体名称
            error: 异常对象
        """
        if agent_name not in self.circuit_breaker_state:
            return
        
        state = self.circuit_breaker_state[agent_name]
        state["errors"] += 1
        state["last_error_time"] = time.time()
        
        # 检查是否需要开启熔断器
        if state["errors"] >= state["threshold"]:
            state["is_open"] = True
            state["next_retry_time"] = time.time() + 30  # 30秒后尝试恢复
            logger.error(f"⚡ 智能体 {agent_name} 熔断器开启！错误次数: {state['errors']}")
        
        # 记录性能指标
        self.performance_monitor.record_request(0, success=False)
    
    def record_success(self, agent_name: str) -> None:
        """记录成功调用，重置熔断器错误计数
        
        Args:
            agent_name: 智能体名称
        """
        if agent_name in self.circuit_breaker_state:
            state = self.circuit_breaker_state[agent_name]
            state["errors"] = 0  # 重置错误计数
            if state["is_open"]:
                state["is_open"] = False
                logger.info(f"✅ 智能体 {agent_name} 熔断器恢复正常")
    
    def create_error_response(self, error: Exception, agent_name: str = "unknown") -> Dict[str, Any]:
        """创建标准的错误响应
        
        Args:
            error: 异常对象
            agent_name: 智能体名称
            
        Returns:
            错误响应字典
        """
        # 使用现有ErrorHandler处理不同类型的错误
        if "oxygent" in str(error).lower():
            error_info = self.error_handler.handle_oxygent_error(error)
        elif "langextract" in str(error).lower():
            error_info = self.error_handler.handle_langextract_error(error)
        else:
            error_info = self.error_handler.handle_general_error(error)
        
        # 记录错误到熔断器
        self.record_error(agent_name, error)
        
        error_message = f"智能体 {agent_name} 执行失败: {error_info['message']}"
        
        return {
            "error": True,
            "error_type": error_info.get('error_type', 'unknown'),
            "message": error_message,
            "suggestion": error_info.get('suggestion', ''),
            "agent_name": agent_name,
            "timestamp": time.time()
        }
    
    def wrap_agent_execution(self, agent_name: str):
        """为智能体执行包装错误处理装饰器
        
        Args:
            agent_name: 智能体名称
            
        Returns:
            装饰器函数
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 检查熔断器状态
                if not self.check_circuit_breaker(agent_name):
                    error_msg = f"智能体 {agent_name} 熔断器开启，暂时不可用"
                    logger.error(error_msg)
                    return {
                        "error": True,
                        "message": error_msg,
                        "agent_name": agent_name,
                        "circuit_breaker": True
                    }
                
                start_time = time.time()
                
                try:
                    # 执行智能体函数
                    result = await func(*args, **kwargs)
                    
                    # 记录成功
                    processing_time = time.time() - start_time
                    self.performance_monitor.record_request(processing_time, success=True)
                    self.record_success(agent_name)
                    
                    logger.info(f"✅ 智能体 {agent_name} 执行成功，耗时 {processing_time:.2f}s")
                    return result
                    
                except Exception as e:
                    # 统一错误处理
                    processing_time = time.time() - start_time
                    self.performance_monitor.record_request(processing_time, success=False)
                    
                    logger.error(f"❌ 智能体 {agent_name} 执行失败，耗时 {processing_time:.2f}s: {e}")
                    
                    # 创建错误响应，让OxyGent框架处理重试
                    return self.create_error_response(e, agent_name)
                    
            return wrapper
        return decorator


class OxyGentAgentFactory:
    """OxyGent智能体工厂，统一配置错误处理"""
    
    def __init__(self, error_handler: OxyGentErrorHandler):
        self.error_handler = error_handler
    
    def create_react_agent_config(self, 
                                name: str,
                                desc: str, 
                                prompt: str,
                                tools: Optional[list] = None,
                                sub_agents: Optional[list] = None,
                                max_react_rounds: int = 3,
                                **kwargs) -> Dict[str, Any]:
        """创建ReActAgent配置，包含错误处理
        
        Args:
            name: 智能体名称
            desc: 智能体描述
            prompt: 系统提示
            tools: 工具列表
            sub_agents: 子智能体列表
            max_react_rounds: 最大React轮数
            **kwargs: 其他参数
            
        Returns:
            完整的智能体配置
        """
        # 获取OxyGent内置错误处理配置
        error_config = self.error_handler.create_oxygent_config(name)
        
        config = {
            "name": name,
            "desc": desc,
            "prompt": prompt,
            "tools": tools or [],
            "sub_agents": sub_agents or [],
            "llm_model": "default_llm",
            "max_react_rounds": max_react_rounds,
            **error_config,  # 包含retries、timeout、semaphore等
            **kwargs
        }
        
        logger.info(f"✅ 创建ReActAgent配置: {name}")
        return config
    
    def create_chat_agent_config(self,
                               name: str,
                               desc: str,
                               prompt: str,
                               **kwargs) -> Dict[str, Any]:
        """创建ChatAgent配置，包含错误处理
        
        Args:
            name: 智能体名称
            desc: 智能体描述  
            prompt: 系统提示
            **kwargs: 其他参数
            
        Returns:
            完整的智能体配置
        """
        # 获取OxyGent内置错误处理配置
        error_config = self.error_handler.create_oxygent_config(name)
        
        config = {
            "name": name,
            "desc": desc,
            "prompt": prompt,
            "llm_model": "default_llm",
            **error_config,  # 包含retries、timeout、semaphore等
            **kwargs
        }
        
        logger.info(f"✅ 创建ChatAgent配置: {name}")
        return config


# 全局错误处理器实例
oxygent_error_handler = OxyGentErrorHandler()
oxygent_agent_factory = OxyGentAgentFactory(oxygent_error_handler)


# 便利函数
def get_error_handler() -> OxyGentErrorHandler:
    """获取全局错误处理器实例"""
    return oxygent_error_handler


def get_agent_factory() -> OxyGentAgentFactory:
    """获取全局智能体工厂实例"""
    return oxygent_agent_factory


def create_smart_error_config(agent_name: str, 
                            retries: int = 2,
                            timeout: int = 60,
                            semaphore: int = 1) -> Dict[str, Any]:
    """快速创建智能错误处理配置
    
    Args:
        agent_name: 智能体名称
        retries: 重试次数
        timeout: 超时时间
        semaphore: 并发控制
        
    Returns:
        错误处理配置字典
    """
    return oxygent_error_handler.create_oxygent_config(
        agent_name, retries, timeout, semaphore
    )


if __name__ == "__main__":
    # 测试错误处理器
    print("🧪 测试OxyGent智能错误处理器")
    
    # 创建错误处理器
    handler = OxyGentErrorHandler()
    factory = OxyGentAgentFactory(handler)
    
    # 测试配置创建
    react_config = factory.create_react_agent_config(
        name="test_react_agent",
        desc="测试ReAct智能体",
        prompt="你是一个测试智能体",
        max_react_rounds=2
    )
    
    chat_config = factory.create_chat_agent_config(
        name="test_chat_agent", 
        desc="测试Chat智能体",
        prompt="你是一个对话智能体"
    )
    
    print(f"✅ ReAct配置: retries={react_config['retries']}, timeout={react_config['timeout']}")
    print(f"✅ Chat配置: retries={chat_config['retries']}, timeout={chat_config['timeout']}")
    
    # 测试熔断器
    print("\n🧪 测试熔断器功能")
    
    # 模拟多次错误
    for i in range(6):
        handler.record_error("test_agent", Exception(f"测试错误 {i+1}"))
        can_execute = handler.check_circuit_breaker("test_agent")
        print(f"错误 {i+1}: 可执行={can_execute}")
    
    # 测试恢复
    handler.record_success("test_agent")
    can_execute = handler.check_circuit_breaker("test_agent")
    print(f"恢复后: 可执行={can_execute}")
    
    print("\n✅ 智能错误处理器测试完成")