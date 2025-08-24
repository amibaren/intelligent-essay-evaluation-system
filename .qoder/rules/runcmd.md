---
trigger: model_decision
description: 多个命令执行时，请拆分成单个命令
---
不要使用这样的命令：“cd "d:\教学智能体项目\智能作文评价系统v0.1" && python utils/message_validator.py”，windows不支持“&&”符号，请拆分执行。