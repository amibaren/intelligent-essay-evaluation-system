"""
性能优化和错误处理模块

提供系统性能监控、优化和错误处理功能
"""

import asyncio
import time
import traceback
from typing import Dict, Any, Optional
from functools import wraps

from loguru import logger
import psutil


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {
            "requests_count": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "error_count": 0,
            "success_count": 0
        }
    
    def record_request(self, processing_time: float, success: bool = True):
        """记录请求性能数据"""
        self.metrics["requests_count"] += 1
        self.metrics["total_processing_time"] += processing_time
        
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
        
        self.metrics["average_processing_time"] = (
            self.metrics["total_processing_time"] / self.metrics["requests_count"]
        )
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network_io": psutil.net_io_counters()._asdict()
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        return {
            "application_metrics": self.metrics,
            "system_metrics": self.get_system_metrics(),
            "timestamp": time.time()
        }


class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_oxygent_error(error: Exception) -> Dict[str, Any]:
        """处理OxyGent相关错误"""
        logger.error(f"OxyGent错误: {error}")
        return {
            "error_type": "oxygent_error",
            "message": str(error),
            "suggestion": "请检查OxyGent配置和API连接"
        }
    
    @staticmethod
    def handle_langextract_error(error: Exception) -> Dict[str, Any]:
        """处理langextract相关错误"""
        logger.error(f"langextract错误: {error}")
        return {
            "error_type": "langextract_error", 
            "message": str(error),
            "suggestion": "请检查langextract API配置和网络连接"
        }
    
    @staticmethod
    def handle_general_error(error: Exception) -> Dict[str, Any]:
        """处理一般错误"""
        logger.error(f"系统错误: {error}")
        logger.error(f"错误详情: {traceback.format_exc()}")
        return {
            "error_type": "system_error",
            "message": str(error),
            "suggestion": "请联系技术支持"
        }


def performance_monitor(monitor: PerformanceMonitor):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                processing_time = time.time() - start_time
                monitor.record_request(processing_time, success)
        
        return wrapper
    return decorator


class OptimizationManager:
    """优化管理器"""
    
    @staticmethod
    async def optimize_concurrent_processing(tasks: list, max_concurrent: int = 4):
        """优化并发处理"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(task):
            async with semaphore:
                return await task
        
        return await asyncio.gather(*[
            process_with_semaphore(task) for task in tasks
        ])
    
    @staticmethod
    def cache_frequently_used_data(cache_size: int = 100):
        """缓存常用数据"""
        from functools import lru_cache
        return lru_cache(maxsize=cache_size)
    
    @staticmethod
    async def batch_process_essays(essays: list, batch_size: int = 5):
        """批量处理作文优化"""
        results = []
        
        for i in range(0, len(essays), batch_size):
            batch = essays[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                # 这里应该是实际的处理函数
                asyncio.sleep(0.1)  # 模拟处理
                for essay in batch
            ])
            results.extend(batch_results)
            
            # 批次间的小延迟，避免API限流
            if i + batch_size < len(essays):
                await asyncio.sleep(0.1)
        
        return results


# 全局性能监控器实例
performance_monitor_instance = PerformanceMonitor()
error_handler_instance = ErrorHandler()
optimization_manager_instance = OptimizationManager()


# 使用示例
@performance_monitor(performance_monitor_instance)
async def example_function():
    """示例函数"""
    await asyncio.sleep(1)  # 模拟处理时间
    return "处理完成"


def setup_error_handling():
    """设置全局错误处理"""
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception