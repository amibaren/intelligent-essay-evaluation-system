# AI作文评审小组 - 基于OxyGent的智能作文评价系统

## 项目简介

本项目基于京东开源的 **OxyGent** 多智能体协作框架和 Google 的 **langextract** 结构化信息提取库，构建了一个"多智能体协作的作文评审小组"系统。通过OxyGent的Oxy原子化组件和MAS(Multi-Agent System)架构，实现六个专业化智能体的协同工作，为小学生提供专业、客观、多维度且充满人文关怀的智能作文批改与反馈服务。

**🌟 设计理念**: 用户可以感知完整的多智能体协作过程，通过MasterAgent统一协调，体验专业化分工的魅力。

## 核心特性

- 🤖 **OxyGent多智能体协作**: 基于京东OxyGent框架的六个专业化智能体分工协作
- 📝 **langextract深度分析**: 使用Google langextract进行结构化文本信息提取
- 🎯 **动态模板生成**: 根据教学目标和作文类型动态生成评价Schema
- 💡 **启发式教学理念**: 注重学生自我发现和思考能力培养
- 📊 **可视化评价报告**: 生成交互式HTML可视化评价报告
- 🔄 **灵活的Oxy组件**: 基于OxyGent的模块化设计，支持灵活扩展
- 🌟 **协作过程透明**: 用户可以观察完整的多智能体协作流程
- 🔒 **智能错误处理**: 内置重试机制、熔断器和性能监控
- 🚀 **资源优化系统**: 智能缓存、并发控制和性能优化
- 📊 **监控告警系统**: 实时系统健康监控和告警机制

## 技术架构

### 核心技术栈
- **多智能体框架**: [OxyGent](https://github.com/jd-opensource/oxygent) - 京东开源的多智能体协作框架
- **信息提取引擎**: [langextract](https://github.com/google/langextract) - Google的结构化信息提取库
- **开发语言**: Python 3.10+
- **LLM支持**: OpenAI GPT-4/Gemini/本地Ollama模型
- **UI界面**: OxyGent内置Web服务

### OxyGent智能体架构
```
MAS (Multi-Agent System)
├── HttpLLM (LLM服务)
├── InstructionalDesigner (ReActAgent) - 教学模板设计师
├── TextAnalyst (ChatAgent) - 文本分析师 (集成langextract)
├── Praiser (ChatAgent) - 赞美鼓励师
├── Guide (ChatAgent) - 启发引导师  
├── Reporter (ReActAgent) - 报告汇总师
└── MasterAgent (ReActAgent) - 主控智能体
```

## 项目结构

```
智能作文评价系统v0.1/
├── README.md                          # 项目说明文档
├── requirements.txt                   # Python依赖列表
├── pyproject.toml                     # 项目配置文件
├── .env.example                       # 环境变量示例
├── main.py                           # 主程序入口(基于OxyGent MAS)
├── doc/                              # 项目文档
│   ├── AI 教学创新项目讨论纪要.md
│   ├── 基于OxyGent与langextract的智能作文评价系统设计方案.md
│   ├── API文档.md
│   └── 部署指南.md
├── oxy_agents/                       # OxyGent原子化组件目录
│   ├── __init__.py
│   ├── llm_config.py                  # LLM配置(基于OxyGent HttpLLM)
│   ├── instructional_designer.py      # 教学模板设计师 (ReActAgent)
│   ├── text_analyst.py                # 文本分析师 (ChatAgent + langextract)
│   ├── praiser.py                     # 赞美鼓励师 (ChatAgent)
│   ├── guide.py                       # 启发引导师 (ChatAgent)
│   ├── reporter.py                    # 报告汇总师 (ReActAgent)
│   └── master_agent.py                # 主控智能体 (ReActAgent)
├── langextract_schemas/              # langextract提取Schema定义
│   ├── __init__.py
│   ├── schema_templates.py            # Schema模板管理器
│   └── schemas/                       # 预定义提取模板
│       ├── basic_writing_schema.py    # 基础写作评价Schema
│       ├── narrative_schema.py        # 记叙文评价Schema
│       └── descriptive_schema.py      # 描写文评价Schema
├── prompts/                          # 智能体提示词库
│   ├── __init__.py
│   ├── designer_prompts.py            # 模板设计师提示词
│   ├── analyst_prompts.py             # 分析师提示词
│   ├── praiser_prompts.py             # 赞美师提示词
│   ├── guide_prompts.py               # 引导师提示词
│   └── reporter_prompts.py            # 报告师提示词
├── utils/                            # 工具模块
│   ├── __init__.py
│   ├── oxygent_error_handler.py       # 智能错误处理系统
│   ├── state_cache_manager.py         # 状态缓存管理器
│   ├── resource_optimizer.py          # 资源优化系统
│   ├── monitoring_system.py           # 监控告警系统
│   ├── message_validator.py           # 消息验证机制
│   ├── workflow_manager.py            # 工作流程管理器
│   ├── text_processor.py              # 文本预处理工具
│   ├── visualization.py               # 可视化工具(langextract.visualize)
│   └── performance.py                 # 性能监控工具
├── tests/                           # 测试代码
│   ├── __init__.py
│   ├── test_agents/                   # 智能体测试
│   ├── test_schemas/                  # Schema测试
│   └── fixtures/                      # 测试数据
│       ├── sample_essays/             # 示例作文
│       └── expected_results/          # 期望结果
├── examples/                        # 使用示例
│   ├── basic_usage.py                # 基础使用示例
│   ├── custom_schema.py              # 自定义Schema示例
│   └── batch_processing.py           # 批量处理示例
├── data/                           # 数据目录
│   ├── essays/                       # 作文数据
│   ├── schemas/                      # 生成的Schema数据
│   └── reports/                      # 生成的评价报告
└── scripts/                        # 脚本工具
    ├── setup_env.py                  # 环境设置脚本
    ├── run_tests.py                  # 测试运行脚本
    └── deploy.py                     # 部署脚本
```

## 第三方模型提供商支持

本系统支持多种第三方大语言模型提供商，包括但不限于：

### 国内提供商
- 🚀 **阿里云通义千问** (Qwen)
- 🧠 **百度文心一言** (ERNIE)
- ✨ **智谱AI** (ChatGLM)
- 🎙️ **讯飞星火** (Spark)
- 🌙 **月之暗面 Kimi** (Moonshot)
- 🔍 **DeepSeek**
- 🔥 **零一万物** (01.AI)
- ☁️ **腾讯混元** (Hunyuan)

### 国外提供商
- 🤖 **OpenAI** (GPT-4, GPT-3.5)
- 🌐 **Google** (Gemini)
- 💬 **Anthropic** (Claude)
- 🏠 **自建服务** (vLLM, Ollama, etc.)

### 配置方法

只需在 `.env` 文件中分别为两个核心模块配置模型信息：

#### OxyGent框架（多智能体系统）
```bash
# 支持OpenAI、Google Gemini、第三方OpenAI兼容API
DEFAULT_LLM_API_KEY=your-api-key
DEFAULT_LLM_BASE_URL=your-base-url  # 如：https://api.openai.com/v1
DEFAULT_LLM_MODEL_NAME=your-model-name  # 如：gpt-4
```

#### langextract模块（结构化信息提取）
```bash
# 可以与OxyGent使用相同配置，也可以单独配置
LANGEXTRACT_API_KEY=your-langextract-api-key
LANGEXTRACT_BASE_URL=your-langextract-base-url  # 如：https://api.openai.com/v1
LANGEXTRACT_MODEL_ID=your-langextract-model-id
```

#### 第三方模型提供商示例
```bash
# 阿里云通义千问（推荐）
DEFAULT_LLM_API_KEY=sk-your-dashscope-api-key
DEFAULT_LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DEFAULT_LLM_MODEL_NAME=qwen-plus
LANGEXTRACT_API_KEY=sk-your-dashscope-api-key
LANGEXTRACT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LANGEXTRACT_MODEL_ID=qwen-plus
```

**更多配置示例**：请查看项目根目录的 `.env.example` 文件，其中包含了各种主流第三方模型提供商的配置示例。

## 快速开始

### 环境要求
- Python 3.10+
- Node.js (可选，用于MCP协议)
- 支持的操作系统: Windows, macOS, Linux

### 安装步骤

1. **克隆项目**
```bash
git clone <项目地址>
cd 智能作文评价系统v0.1
```

2. **创建虚拟环境**
```bash
# 使用conda
conda create -n essay_eval_env python==3.10
conda activate essay_eval_env

# 或使用uv(推荐)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install 3.10
uv venv .venv --python 3.10
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **安装依赖**
```bash
# 使用pip
pip install -r requirements.txt

# 或使用uv(推荐)
uv pip install -r requirements.txt
```

4. **配置环境变量**
```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，分别为两个模块配置
# OxyGent框架配置
export DEFAULT_LLM_API_KEY="your-api-key"
export DEFAULT_LLM_BASE_URL="your-base-url"
export DEFAULT_LLM_MODEL_NAME="your-model"

# langextract模块配置
export LANGEXTRACT_API_KEY="your-langextract-api-key"
export LANGEXTRACT_BASE_URL="your-langextract-base-url"
export LANGEXTRACT_MODEL_ID="your-langextract-model"
```

**🔒 安全提示**: 
- `.env`文件包含敏感的API密钥，已从 Git 仓库中移除
- 请务必保护好您的API密钥，不要将其上传到公开仓库
- 建议使用环境变量或密钥管理工具来管理敏感信息

5. **验证配置**
```bash
# 验证配置是否正确
python scripts/validate_config.py
```

6. **运行系统**
```bash
python main.py
```

系统将启动OxyGent Web服务，默认在 http://localhost:8080 提供交互界面。

## 使用说明

### 基本工作流程

1. **配置评价模板**: 教师通过自然语言与"教学模板设计师"对话，确定评价重点
2. **提交作文**: 上传需要评价的学生作文
3. **智能分析**: 系统自动完成文本分析和多维度评价
4. **生成报告**: 输出包含表扬、建议和指导的综合评价报告

### 核心功能

- **动态模板生成**: 根据教学目标自动生成评价模板
- **多维度分析**: 从基础规范、内容结构、语言亮点等多个维度分析
- **人性化反馈**: 既有客观分析，又有温暖鼓励和启发引导
- **批量处理**: 支持批量处理多篇作文

## 开发指南

### 添加新的智能体

1. 在 `src/agents/` 目录下创建新的智能体文件
2. 继承 `BaseAgent` 基类
3. 实现必要的方法
4. 在工作流中注册新智能体

### 自定义评价模板

1. 在 `src/templates/schemas/` 目录下创建新的JSON模板文件
2. 定义评价维度和字段
3. 通过模板管理器加载和使用

## 测试

运行所有测试：
```bash
python scripts/run_tests.py
```

运行特定测试：
```bash
python -m pytest tests/test_agents/ -v
```

## 贡献指南

1. Fork 本项目
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

## 联系方式

- 项目维护者: [您的姓名]
- 邮箱: [您的邮箱]
- 项目地址: [项目地址]

## 更新日志

### v0.1.2 (2025-08-24) - 安全优化
- 🔒 **安全改进**: 从 Git 仓库中移除 .env 文件，保护敏感信息
- 🛡️ **防泼露机制**: 完善 .gitignore 配置，防止意外上传敏感文件
- 📝 **开发指南**: 更新环境配置说明，提供安全最佳实践

### v0.1.1 (2025-08-24) - 重大架构重构
- 🎆 **多智能体协作优化**: 实现用户感知的协作过程
- 🤖 **MasterAgent 增强**: 作为唯一用户交互入口，协调各专业智能体
- 🔧 **智能错误处理**: 新增重试机制、熔断器和错误恢复
- 🚀 **资源优化系统**: 智能缓存、并发控制和性能优化
- 📊 **监控告警系统**: 实时系统健康监控和告警机制
- ⚙️ **工作流程管理**: 标准化的智能体协作流程
- 💬 **消息验证机制**: 确保智能体间通信格式一致

### v0.1.0 (2025-08-23) - 初始版本
- 🎉 初始版本发布
- 🔨 实现基础的多智能体协作框架
- 🔗 集成 langextract 文本分析功能
- 🌐 提供 OxyGent UI 支持