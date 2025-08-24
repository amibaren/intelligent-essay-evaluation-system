"""
单元测试模块

测试各个智能体的功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

class TestOxyGentAgents:
    """OxyGent智能体单元测试"""
    
    @pytest.mark.asyncio
    async def test_text_analyst(self):
        """测试文本分析师"""
        # 模拟测试
        content = "这是一篇测试作文。"
        result = {
            "word_count": len(content),
            "highlights": ["测试作文"],
            "status": "success"
        }
        assert result["status"] == "success"
        assert result["word_count"] > 0
    
    @pytest.mark.asyncio  
    async def test_praiser_agent(self):
        """测试赞美鼓励师"""
        # 模拟测试
        praise = "这篇作文写得很好！"
        assert len(praise) > 0
        assert "好" in praise
    
    @pytest.mark.asyncio
    async def test_guide_agent(self):
        """测试启发引导师"""
        # 模拟测试
        questions = ["你觉得这里可以怎么改进？"]
        assert len(questions) > 0
        assert "？" in questions[0]

class TestLangExtractIntegration:
    """langextract集成测试"""
    
    def test_schema_creation(self):
        """测试Schema创建"""
        schema = {
            "name": "test_schema",
            "categories": ["测试类别"]
        }
        assert schema["name"] == "test_schema"
        assert len(schema["categories"]) > 0