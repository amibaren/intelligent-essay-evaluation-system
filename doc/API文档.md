# API文档

## 概述

基于OxyGent和langextract的AI作文评审小组API文档。

## 核心组件

### 1. OxyGent MAS系统

#### 启动系统
```python
from oxygent import MAS
async with MAS(oxy_space=oxy_space) as mas:
    await mas.start_web_service()
```

#### 调用智能体
```python
result = await mas.call(
    callee="agent_name",
    arguments={"query": "输入内容"}
)
```

### 2. langextract分析

#### 基本使用
```python
import langextract as lx
import os

# 从环境变量获取配置
model_id = os.getenv("LANGEXTRACT_MODEL_ID") or os.getenv("DEFAULT_LLM_MODEL_NAME") or "gemini-2.5-flash"
api_key = os.getenv("LANGEXTRACT_API_KEY") or os.getenv("DEFAULT_LLM_API_KEY")

result = lx.extract(
    text_or_documents=text,
    prompt_description=prompt,
    examples=examples,
    model_id=model_id,
    api_key=api_key  # 如果需要
)
```

## 智能体接口

### 教学模板设计师
- **功能**: 生成评价模板
- **输入**: 教师需求、作文类型、年级
- **输出**: 评价Schema

### 文本分析师  
- **功能**: 结构化文本分析
- **输入**: 作文内容、评价模板
- **输出**: 分析数据

### 赞美鼓励师
- **功能**: 生成表扬内容
- **输入**: 分析结果
- **输出**: 鼓励文本

### 启发引导师
- **功能**: 生成引导问题
- **输入**: 分析结果
- **输出**: 启发问题

### 报告汇总师
- **功能**: 生成最终报告
- **输入**: 所有评价结果
- **输出**: 综合报告

## 使用示例

```python
# 基础使用
python examples/basic_usage.py

# 集成测试
python tests/integration_test.py
```