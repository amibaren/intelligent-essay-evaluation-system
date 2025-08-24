#!/usr/bin/env python3
"""
智能体消息格式验证和转换工具

解决OxyGent框架中智能体间消息传递的格式问题
消除"跳过空消息"警告，确保消息格式统一
"""

import json
from typing import Dict, List, Any, Optional, Union
from loguru import logger
from oxygent import OxyRequest, OxyResponse


class MessageValidator:
    """消息格式验证和转换器"""
    
    def __init__(self):
        self.name = "message_validator"
        
    @staticmethod
    def validate_and_fix_message(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """验证并修复单条消息格式
        
        Args:
            message: 原始消息字典
            
        Returns:
            修复后的消息，如果无法修复返回None
        """
        if not isinstance(message, dict):
            logger.warning(f"⚠️ 消息类型错误: {type(message)}, 尝试转换")
            if hasattr(message, '__dict__'):
                message = message.__dict__
            else:
                return None
        
        # 确保必要字段存在
        role = message.get('role', 'user')
        content = message.get('content', '')
        
        # 处理content字段的各种情况
        if content is None:
            content = ""
        elif not isinstance(content, str):
            # 尝试转换为字符串
            try:
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, ensure_ascii=False)
                else:
                    content = str(content)
            except Exception as e:
                logger.warning(f"⚠️ 内容转换失败: {e}")
                content = ""
        
        # 清理内容
        content = content.strip()
        
        # 如果内容仍然为空，尝试从其他字段获取
        if not content:
            # 检查是否有其他可能包含内容的字段
            for field in ['text', 'query', 'data', 'result', 'output']:
                if field in message and message[field]:
                    try:
                        content = str(message[field]).strip()
                        if content:
                            logger.info(f"✅ 从字段 '{field}' 恢复消息内容")
                            break
                    except Exception:
                        continue
        
        # 如果还是为空，根据角色提供默认内容
        if not content:
            if role == 'system':
                content = "系统提示已加载。"
            elif role == 'assistant':
                content = "正在处理您的请求..."
            else:  # user or other
                content = "请继续处理当前任务。"
            
            logger.info(f"✅ 为 {role} 角色提供默认内容")
        
        return {
            "role": role,
            "content": content
        }
    
    @staticmethod
    def validate_and_fix_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """验证并修复消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            修复后的消息列表
        """
        if not isinstance(messages, list):
            logger.error(f"❌ 消息格式错误: 期望列表，得到 {type(messages)}")
            return []
        
        fixed_messages = []
        
        for i, msg in enumerate(messages):
            fixed_msg = MessageValidator.validate_and_fix_message(msg)
            if fixed_msg:
                fixed_messages.append(fixed_msg)
            else:
                logger.warning(f"⚠️ 跳过无法修复的消息 位置{i}: {msg}")
        
        # 确保至少有一条消息
        if not fixed_messages:
            logger.warning("⚠️ 没有有效消息，创建默认用户消息")
            fixed_messages.append({
                "role": "user",
                "content": "请帮助处理当前任务。"
            })
        
        # 确保消息格式符合OpenAI标准
        # 第一条消息应该是system或user
        if fixed_messages and fixed_messages[0]['role'] not in ['system', 'user']:
            logger.info("🔧 调整消息顺序，确保符合标准格式")
            # 在开头添加用户消息
            fixed_messages.insert(0, {
                "role": "user", 
                "content": "开始处理任务。"
            })
        
        return fixed_messages


class OxyRequestHelper:
    """OxyRequest处理助手"""
    
    @staticmethod
    def ensure_valid_query(oxy_request: OxyRequest) -> OxyRequest:
        """确保OxyRequest包含有效的查询内容
        
        Args:
            oxy_request: 原始请求
            
        Returns:
            修复后的请求
        """
        try:
            # 获取查询内容
            current_query = oxy_request.get_query() if hasattr(oxy_request, 'get_query') else ""
            
            # 如果查询为空，尝试从arguments构建
            if not current_query or current_query.strip() == "":
                if hasattr(oxy_request, 'arguments') and oxy_request.arguments:
                    args = oxy_request.arguments
                    
                    # 尝试从常见参数构建查询
                    if 'essay_content' in args:
                        query_parts = []
                        if 'query_type' in args:
                            query_parts.append(f"任务类型: {args['query_type']}")
                        if 'essay_type' in args:
                            query_parts.append(f"作文类型: {args['essay_type']}")
                        if 'grade_level' in args:
                            query_parts.append(f"年级: {args['grade_level']}")
                        
                        query_parts.append(f"作文内容: {args['essay_content'][:200]}...")
                        
                        new_query = "\n".join(query_parts)
                        oxy_request.set_query(new_query)
                        logger.info("✅ 从arguments重建查询内容")
                    
                    elif 'query' in args:
                        oxy_request.set_query(str(args['query']))
                        logger.info("✅ 从arguments.query恢复查询内容")
                    
                    else:
                        # 创建通用查询
                        oxy_request.set_query("请根据提供的参数处理当前任务。")
                        logger.info("✅ 设置默认查询内容")
            
            return oxy_request
            
        except Exception as e:
            logger.error(f"❌ 处理OxyRequest失败: {e}")
            return oxy_request


def create_validation_middleware():
    """创建消息验证中间件
    
    这个函数可以被集成到OxyGent的处理流程中
    """
    def middleware(oxy_request: OxyRequest) -> OxyRequest:
        """消息验证中间件"""
        try:
            # 确保请求包含有效查询
            oxy_request = OxyRequestHelper.ensure_valid_query(oxy_request)
            
            logger.debug("✅ 消息验证中间件处理完成")
            return oxy_request
            
        except Exception as e:
            logger.error(f"❌ 消息验证中间件失败: {e}")
            return oxy_request
    
    return middleware


if __name__ == "__main__":
    # 测试消息验证器
    print("🧪 测试消息验证器")
    
    # 测试各种问题消息
    test_messages = [
        {"role": "user", "content": ""},  # 空内容
        {"role": "assistant", "content": None},  # None内容
        {"role": "system", "content": {"data": "test"}},  # 字典内容
        {"role": "user", "text": "这是文本字段"},  # 错误字段名
        "invalid_message",  # 非字典
        {"content": "没有role字段"},  # 缺少role
    ]
    
    print("原始消息:")
    for i, msg in enumerate(test_messages):
        print(f"  {i+1}. {msg}")
    
    # 验证和修复
    validator = MessageValidator()
    fixed_messages = validator.validate_and_fix_messages(test_messages)
    
    print("\n修复后的消息:")
    for i, msg in enumerate(fixed_messages):
        print(f"  {i+1}. {msg}")
    
    print(f"\n✅ 成功修复 {len(fixed_messages)} 条消息")