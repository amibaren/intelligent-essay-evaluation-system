#!/usr/bin/env python3
"""
OxyGent系统监控和告警机制

实现详细的状态转换监控、异常告警和graceful degradation能力
确保系统稳定运行和故障恢复
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque
import psutil
import threading
from loguru import logger


class AlertLevel(Enum):
    """告警级别"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class SystemHealth(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警信息"""
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: float
    metadata: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class HealthMetrics:
    """健康指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    active_agents: int
    error_rate: float
    response_time: float
    success_rate: float
    component_status: Dict[str, SystemHealth]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['component_status'] = {k: v.value for k, v in self.component_status.items()}
        return data


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, alert_thresholds: Optional[Dict[str, Any]] = None):
        self.monitoring = False
        self.monitor_task = None
        self.alerts: List[Alert] = []
        self.health_history: deque = deque(maxlen=1000)  # 保留最近1000条记录
        self.component_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # 设置默认告警阈值
        self.alert_thresholds = alert_thresholds or {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'error_rate': 0.1,  # 10%
            'response_time': 30.0,  # 30秒
            'success_rate': 0.9,  # 90%
            'agent_timeout': 120.0  # 2分钟
        }
        
        # 组件健康状态
        self.component_health: Dict[str, SystemHealth] = {
            'llm_service': SystemHealth.HEALTHY,
            'database': SystemHealth.HEALTHY,
            'cache_system': SystemHealth.HEALTHY,
            'task_queue': SystemHealth.HEALTHY,
            'agents': SystemHealth.HEALTHY
        }
        
        # 统计计数器
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'agent_calls': defaultdict(int),
            'error_counts': defaultdict(int)
        }
        
        self.lock = threading.Lock()
    
    async def start_monitoring(self, interval: float = 30.0):
        """开始监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info(f"🔍 系统监控启动，监控间隔: {interval}s")
    
    async def stop_monitoring(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 系统监控已停止")
    
    async def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集健康指标
                metrics = self._collect_health_metrics()
                self.health_history.append(metrics)
                
                # 检查告警条件
                await self._check_alerts(metrics)
                
                # 更新组件健康状态
                self._update_component_health(metrics)
                
                # 等待下一个监控周期
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                await asyncio.sleep(interval)
    
    def _collect_health_metrics(self) -> HealthMetrics:
        """收集健康指标"""
        with self.lock:
            # 系统资源
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            # 计算错误率和成功率
            total_requests = self.stats['total_requests']
            if total_requests > 0:
                error_rate = self.stats['failed_requests'] / total_requests
                success_rate = self.stats['successful_requests'] / total_requests
                avg_response_time = self.stats['total_response_time'] / total_requests
            else:
                error_rate = 0.0
                success_rate = 1.0
                avg_response_time = 0.0
            
            # 活跃智能体数量（从组件统计获取）
            active_agents = sum(
                stats.get('active_count', 0) 
                for stats in self.component_stats.values()
            )
            
            return HealthMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                active_agents=active_agents,
                error_rate=error_rate,
                response_time=avg_response_time,
                success_rate=success_rate,
                component_status=self.component_health.copy()
            )
    
    async def _check_alerts(self, metrics: HealthMetrics):
        """检查告警条件"""
        # CPU告警
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            await self._create_alert(
                AlertLevel.WARNING,
                "CPU使用率过高",
                f"CPU使用率达到 {metrics.cpu_percent:.1f}%",
                "system",
                {'cpu_percent': metrics.cpu_percent}
            )
        
        # 内存告警
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            await self._create_alert(
                AlertLevel.WARNING,
                "内存使用率过高",
                f"内存使用率达到 {metrics.memory_percent:.1f}%",
                "system",
                {'memory_percent': metrics.memory_percent}
            )
        
        # 错误率告警
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            await self._create_alert(
                AlertLevel.ERROR,
                "错误率过高",
                f"错误率达到 {metrics.error_rate:.1%}",
                "agents",
                {'error_rate': metrics.error_rate}
            )
        
        # 响应时间告警
        if metrics.response_time > self.alert_thresholds['response_time']:
            await self._create_alert(
                AlertLevel.WARNING,
                "响应时间过长",
                f"平均响应时间达到 {metrics.response_time:.1f}s",
                "performance",
                {'response_time': metrics.response_time}
            )
        
        # 成功率告警
        if metrics.success_rate < self.alert_thresholds['success_rate']:
            await self._create_alert(
                AlertLevel.ERROR,
                "成功率过低",
                f"成功率仅为 {metrics.success_rate:.1%}",
                "agents",
                {'success_rate': metrics.success_rate}
            )
    
    def _update_component_health(self, metrics: HealthMetrics):
        """更新组件健康状态"""
        # 根据指标更新组件健康状态
        if metrics.error_rate > 0.5:  # 50%错误率
            self.component_health['agents'] = SystemHealth.CRITICAL
        elif metrics.error_rate > 0.2:  # 20%错误率
            self.component_health['agents'] = SystemHealth.UNHEALTHY
        elif metrics.error_rate > 0.1:  # 10%错误率
            self.component_health['agents'] = SystemHealth.DEGRADED
        else:
            self.component_health['agents'] = SystemHealth.HEALTHY
        
        # 系统资源健康状态
        if metrics.cpu_percent > 90 or metrics.memory_percent > 90:
            system_health = SystemHealth.CRITICAL
        elif metrics.cpu_percent > 80 or metrics.memory_percent > 85:
            system_health = SystemHealth.UNHEALTHY
        elif metrics.cpu_percent > 70 or metrics.memory_percent > 75:
            system_health = SystemHealth.DEGRADED
        else:
            system_health = SystemHealth.HEALTHY
        
        self.component_health['system'] = system_health
    
    async def _create_alert(self, 
                          level: AlertLevel, 
                          title: str, 
                          message: str, 
                          component: str, 
                          metadata: Dict[str, Any]):
        """创建告警"""
        # 避免重复告警（同一组件同一类型5分钟内只告警一次）
        recent_alerts = [
            alert for alert in self.alerts
            if (time.time() - alert.timestamp < 300 and  # 5分钟内
                alert.component == component and
                alert.title == title and
                not alert.resolved)
        ]
        
        if recent_alerts:
            return  # 避免重复告警
        
        alert = Alert(
            level=level,
            title=title,
            message=message,
            component=component,
            timestamp=time.time(),
            metadata=metadata
        )
        
        self.alerts.append(alert)
        
        # 触发告警处理器
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"❌ 告警处理器错误: {e}")
        
        # 记录告警日志
        log_level = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }[level]
        
        log_level(f"🚨 [{component}] {title}: {message}")
    
    def record_request(self, success: bool, response_time: float, agent_name: str = "unknown"):
        """记录请求统计"""
        with self.lock:
            self.stats['total_requests'] += 1
            self.stats['total_response_time'] += response_time
            self.stats['agent_calls'][agent_name] += 1
            
            if success:
                self.stats['successful_requests'] += 1
            else:
                self.stats['failed_requests'] += 1
                self.stats['error_counts'][agent_name] += 1
    
    def record_component_status(self, component: str, status: Dict[str, Any]):
        """记录组件状态"""
        with self.lock:
            self.component_stats[component] = {
                **status,
                'last_update': time.time()
            }
    
    def get_system_health(self) -> SystemHealth:
        """获取整体系统健康状态"""
        health_levels = list(self.component_health.values())
        
        if SystemHealth.CRITICAL in health_levels:
            return SystemHealth.CRITICAL
        elif SystemHealth.UNHEALTHY in health_levels:
            return SystemHealth.UNHEALTHY
        elif SystemHealth.DEGRADED in health_levels:
            return SystemHealth.DEGRADED
        else:
            return SystemHealth.HEALTHY
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: int) -> bool:
        """解决告警"""
        if 0 <= alert_id < len(self.alerts):
            alert = self.alerts[alert_id]
            if not alert.resolved:
                alert.resolved = True
                alert.resolution_time = time.time()
                logger.info(f"✅ 告警已解决: {alert.title}")
                return True
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取监控仪表板数据"""
        current_metrics = self.health_history[-1] if self.health_history else None
        
        with self.lock:
            stats_copy = self.stats.copy()
            component_stats_copy = dict(self.component_stats)
        
        return {
            'system_health': self.get_system_health().value,
            'current_metrics': current_metrics.to_dict() if current_metrics else None,
            'active_alerts': [alert.to_dict() for alert in self.get_active_alerts()],
            'component_health': {k: v.value for k, v in self.component_health.items()},
            'statistics': stats_copy,
            'component_stats': component_stats_copy,
            'alert_count': len(self.get_active_alerts()),
            'total_alerts': len(self.alerts),
            'uptime': time.time() - (self.health_history[0].timestamp if self.health_history else time.time())
        }
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.alert_handlers.append(handler)


class GracefulDegradationManager:
    """优雅降级管理器"""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.degradation_rules: Dict[str, Callable] = {}
        self.active_degradations: Dict[str, Dict[str, Any]] = {}
        
        # 设置默认降级规则
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """设置默认降级规则"""
        self.degradation_rules = {
            'high_cpu': self._handle_high_cpu,
            'high_memory': self._handle_high_memory,
            'high_error_rate': self._handle_high_error_rate,
            'slow_response': self._handle_slow_response,
            'agent_failure': self._handle_agent_failure
        }
    
    async def check_degradation_conditions(self):
        """检查降级条件"""
        if not self.monitor.health_history:
            return
        
        current_metrics = self.monitor.health_history[-1]
        
        # 检查各种降级条件
        if current_metrics.cpu_percent > 90:
            await self._apply_degradation('high_cpu', current_metrics)
        
        if current_metrics.memory_percent > 90:
            await self._apply_degradation('high_memory', current_metrics)
        
        if current_metrics.error_rate > 0.3:  # 30%错误率
            await self._apply_degradation('high_error_rate', current_metrics)
        
        if current_metrics.response_time > 60:  # 60秒响应时间
            await self._apply_degradation('slow_response', current_metrics)
    
    async def _apply_degradation(self, rule_name: str, metrics: HealthMetrics):
        """应用降级策略"""
        if rule_name in self.active_degradations:
            return  # 已经在降级中
        
        logger.warning(f"⚡ 触发降级策略: {rule_name}")
        
        if rule_name in self.degradation_rules:
            degradation_info = await self.degradation_rules[rule_name](metrics)
            self.active_degradations[rule_name] = {
                'start_time': time.time(),
                'metrics': metrics.to_dict(),
                'info': degradation_info
            }
    
    async def _handle_high_cpu(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """处理高CPU使用率"""
        return {
            'action': 'reduce_concurrency',
            'description': '降低并发处理数量',
            'parameters': {'max_concurrent_agents': 1}
        }
    
    async def _handle_high_memory(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """处理高内存使用率"""
        return {
            'action': 'clear_caches',
            'description': '清理缓存和临时数据',
            'parameters': {'force_gc': True}
        }
    
    async def _handle_high_error_rate(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """处理高错误率"""
        return {
            'action': 'fallback_mode',
            'description': '启用备用处理模式',
            'parameters': {'simplified_processing': True}
        }
    
    async def _handle_slow_response(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """处理慢响应"""
        return {
            'action': 'timeout_reduction',
            'description': '减少超时时间',
            'parameters': {'timeout': 30}
        }
    
    async def _handle_agent_failure(self, metrics: HealthMetrics) -> Dict[str, Any]:
        """处理智能体故障"""
        return {
            'action': 'agent_bypass',
            'description': '绕过故障智能体',
            'parameters': {'use_fallback_agent': True}
        }
    
    def recover_from_degradation(self, rule_name: str) -> bool:
        """从降级状态恢复"""
        if rule_name in self.active_degradations:
            degradation_info = self.active_degradations[rule_name]
            duration = time.time() - degradation_info['start_time']
            
            del self.active_degradations[rule_name]
            logger.info(f"✅ 从降级状态恢复: {rule_name} (持续 {duration:.1f}s)")
            return True
        return False
    
    def get_degradation_status(self) -> Dict[str, Any]:
        """获取降级状态"""
        return {
            'active_degradations': len(self.active_degradations),
            'degradations': self.active_degradations.copy(),
            'available_rules': list(self.degradation_rules.keys())
        }


# 全局监控器实例
system_monitor = SystemMonitor()
degradation_manager = GracefulDegradationManager(system_monitor)


def get_system_monitor() -> SystemMonitor:
    """获取全局系统监控器"""
    return system_monitor


def get_degradation_manager() -> GracefulDegradationManager:
    """获取全局降级管理器"""
    return degradation_manager


def setup_default_alert_handlers():
    """设置默认告警处理器"""
    def log_alert_handler(alert: Alert):
        """日志告警处理器"""
        level_emojis = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        
        emoji = level_emojis.get(alert.level, "🔔")
        logger.info(f"{emoji} 告警: [{alert.component}] {alert.title} - {alert.message}")
    
    system_monitor.add_alert_handler(log_alert_handler)


async def initialize_monitoring_system():
    """初始化监控系统"""
    setup_default_alert_handlers()
    await system_monitor.start_monitoring(interval=30.0)
    logger.info("🔍 监控系统初始化完成")


async def cleanup_monitoring_system():
    """清理监控系统"""
    await system_monitor.stop_monitoring()
    logger.info("🏁 监控系统清理完成")


if __name__ == "__main__":
    # 测试监控系统
    print("🧪 测试系统监控")
    
    async def test_monitoring():
        # 初始化监控
        await initialize_monitoring_system()
        
        # 等待一些监控数据
        await asyncio.sleep(35)
        
        # 获取仪表板数据
        dashboard = system_monitor.get_dashboard_data()
        print(f"系统健康状态: {dashboard['system_health']}")
        print(f"活跃告警数量: {dashboard['alert_count']}")
        print(f"组件健康状态: {dashboard['component_health']}")
        
        # 模拟一些请求
        for i in range(10):
            success = i % 3 != 0  # 模拟70%成功率
            response_time = 1.0 + (i % 5) * 0.5
            system_monitor.record_request(success, response_time, f"test_agent_{i%3}")
        
        # 检查降级条件
        await degradation_manager.check_degradation_conditions()
        
        degradation_status = degradation_manager.get_degradation_status()
        print(f"降级状态: {degradation_status}")
        
        # 清理
        await cleanup_monitoring_system()
    
    # 运行测试
    asyncio.run(test_monitoring())
    print("\n✅ 监控系统测试完成")