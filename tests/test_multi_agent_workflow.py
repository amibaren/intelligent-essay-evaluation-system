#!/usr/bin/env python3
"""
测试多智能体协作流程

验证修改后的MasterAgent、InstructionalDesigner、Reporter等的协作机制
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from loguru import logger

# 测试用例数据
TEST_ESSAY = """
我的小狗

我家有一只可爱的小狗，名字叫豆豆。它有着金黄色的毛发，就像秋天的阳光一样温暖。
豆豆的眼睛圆圆的，黑亮黑亮的，总是好奇地看着周围的一切。它的尾巴摇起来像一个小风扇，
特别是看见我回家的时候，摇得更加起劲了。

每天早上，豆豆都会陪我上学。它总是在门口等着我，用那双水汪汪的大眼睛看着我，好像在说：
"小主人，要好好学习哦！"放学回家的时候，远远地就能看见豆豆在门口摇着尾巴迎接我。

豆豆很聪明，会做很多有趣的事情。它会握手、坐下、装死，还会帮我叼拖鞋呢！有一次，
妈妈找不到手机了，豆豆居然用鼻子嗅了嗅，然后跑到沙发下面，把手机给找出来了。
妈妈夸它真是个小侦探。

我最喜欢和豆豆一起玩的时候。每个周末，我都会带它到公园里跑步。豆豆跑得很快，
有时候还会回头看看我有没有跟上。累了的时候，我们就一起坐在草地上休息，
我摸着它的头，它就会安静地趴在我身边。

豆豆已经陪伴我两年了，它不仅是我的宠物，更像是我的朋友。我希望豆豆能够健康快乐，
永远陪在我身边。
"""

TEST_CASE = {
    "student_name": "小明",
    "grade_level": "三年级",
    "essay_title": "我的小狗",
    "essay_type": "记叙文",
    "essay_content": TEST_ESSAY.strip(),
    "teaching_focus": "动物描写、情感表达"
}


def create_test_query(test_case: dict) -> str:
    """
    创建测试查询
    """
    return f"""
老师您好！请为以下作文进行评价：

**学生信息：**
- 姓名：{test_case['student_name']}
- 年级：{test_case['grade_level']}
- 作文题目：{test_case['essay_title']}
- 作文类型：{test_case['essay_type']}
- 教学重点：{test_case['teaching_focus']}

**作文内容：**
{test_case['essay_content']}

请AI作文评审小组进行专业评价。
"""


def analyze_workflow_response(response: str) -> dict:
    """
    分析工作流程响应，检查是否按预期执行
    """
    analysis = {
        "immediate_response": False,
        "instructional_designer_called": False,
        "reporter_called": False,
        "sub_agents_coordinated": False,
        "final_report_generated": False,
        "progress_feedback": False,
        "response_quality": "unknown"
    }
    
    response_lower = response.lower()
    
    # 检查是否立即响应
    immediate_indicators = [
        "收到您的作文",
        "马上安排专业团队",
        "开始处理",
        "立即开始"
    ]
    analysis["immediate_response"] = any(indicator in response for indicator in immediate_indicators)
    
    # 检查是否调用了instructional_designer
    designer_indicators = [
        "instructional_designer",
        "模板设计师",
        "生成评价模板",
        "评价标准"
    ]
    analysis["instructional_designer_called"] = any(indicator in response_lower for indicator in designer_indicators)
    
    # 检查是否调用了reporter
    reporter_indicators = [
        "reporter",
        "报告汇总师",
        "生成综合报告",
        "专业团队正在"
    ]
    analysis["reporter_called"] = any(indicator in response_lower for indicator in reporter_indicators)
    
    # 检查是否协调了子智能体
    sub_agent_indicators = [
        "text_analyst",
        "praiser",
        "guide",
        "文本分析师",
        "赞美鼓励师",
        "启发引导师",
        "多维度分析"
    ]
    analysis["sub_agents_coordinated"] = any(indicator in response_lower for indicator in sub_agent_indicators)
    
    # 检查是否生成了最终报告
    report_indicators = [
        "综合评价报告",
        "亮点发现",
        "客观分析",
        "成长建议",
        "markdown",
        "可视化"
    ]
    analysis["final_report_generated"] = any(indicator in response for indicator in report_indicators)
    
    # 检查是否有进度反馈
    progress_indicators = [
        "正在",
        "请稍等",
        "马上",
        "开始",
        "进行中"
    ]
    analysis["progress_feedback"] = any(indicator in response for indicator in progress_indicators)
    
    # 评估响应质量
    if analysis["final_report_generated"] and analysis["sub_agents_coordinated"]:
        analysis["response_quality"] = "excellent"
    elif analysis["immediate_response"] and (analysis["instructional_designer_called"] or analysis["reporter_called"]):
        analysis["response_quality"] = "good"
    elif analysis["immediate_response"]:
        analysis["response_quality"] = "fair"
    else:
        analysis["response_quality"] = "poor"
    
    return analysis


def generate_test_report(analysis: dict, response: str, test_case: dict) -> str:
    """
    生成测试报告
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# 多智能体协作流程测试报告

**测试时间：** {timestamp}
**测试用例：** {test_case['essay_title']} - {test_case['grade_level']}

## 🎯 测试目标
验证修改后的多智能体协作流程是否按预期工作：
1. MasterAgent能否主动响应并立即开始协调
2. InstructionalDesigner是否被正确调用生成评价模板
3. Reporter是否协调sub_agents完成分析
4. 整个流程是否顺畅无阻

## 📊 测试结果分析

### ✅ 通过的检查项
"""

    # 添加通过的检查项
    checks = [
        ("immediate_response", "立即响应", "MasterAgent能够立即响应用户请求"),
        ("instructional_designer_called", "调用设计师", "正确调用InstructionalDesigner生成评价模板"),
        ("reporter_called", "调用报告师", "正确调用Reporter进行综合分析"),
        ("sub_agents_coordinated", "协调子智能体", "Reporter成功协调sub_agents进行多维度分析"),
        ("final_report_generated", "生成最终报告", "成功生成完整的评价报告"),
        ("progress_feedback", "进度反馈", "为用户提供适当的进度反馈")
    ]
    
    passed_checks = []
    failed_checks = []
    
    for key, name, description in checks:
        if analysis[key]:
            passed_checks.append(f"- ✅ **{name}**: {description}")
        else:
            failed_checks.append(f"- ❌ **{name}**: {description}")
    
    if passed_checks:
        report += "\n".join(passed_checks)
    else:
        report += "- 无通过项"
    
    report += "\n\n### ❌ 未通过的检查项\n"
    
    if failed_checks:
        report += "\n".join(failed_checks)
    else:
        report += "- 全部通过 🎉"
    
    report += f"""

## 📈 整体评估

**响应质量：** {analysis['response_quality'].upper()}

**质量说明：**
- **EXCELLENT**: 完整的工作流程，生成了最终报告
- **GOOD**: 正确开始协调流程，调用了主要智能体
- **FAIR**: 能够立即响应，但流程不完整
- **POOR**: 响应延迟或流程异常

## 🔧 改进建议

"""

    # 根据分析结果提供改进建议
    if analysis["response_quality"] == "poor":
        report += """
- 🚨 **紧急**: MasterAgent未能正确响应，请检查系统提示词和配置
- 检查环境变量配置是否正确
- 验证所有智能体是否正确注册
"""
    elif analysis["response_quality"] == "fair":
        report += """
- ⚠️ **重要**: 虽然能够响应，但协作流程不完整
- 检查MasterAgent的sub_agents调用逻辑
- 确认智能体之间的数据传递是否正常
"""
    elif analysis["response_quality"] == "good":
        report += """
- ✅ **良好**: 基本流程正常，可能需要微调
- 检查是否所有sub_agents都被正确协调
- 确认最终报告生成逻辑
"""
    else:
        report += """
- 🎉 **优秀**: 工作流程完整，协作机制正常
- 可以考虑优化响应速度和用户体验
- 监控实际使用中的表现
"""

    report += f"""

## 📝 实际响应内容

```
{response[:1000]}{'...' if len(response) > 1000 else ''}
```

## 🧪 测试用例详情

**作文标题：** {test_case['essay_title']}
**学生年级：** {test_case['grade_level']}
**作文类型：** {test_case['essay_type']}
**教学重点：** {test_case['teaching_focus']}
**作文字数：** {len(test_case['essay_content'])}字

---

*该报告由多智能体协作流程测试工具自动生成*
"""

    return report


def save_test_results(analysis: dict, response: str, test_case: dict) -> str:
    """
    保存测试结果
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存详细结果为JSON
    results = {
        "timestamp": timestamp,
        "test_case": test_case,
        "analysis": analysis,
        "response": response,
        "response_length": len(response)
    }
    
    results_path = f"tests/results/workflow_test_{timestamp}.json"
    Path(results_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 生成测试报告
    report = generate_test_report(analysis, response, test_case)
    report_path = f"tests/results/workflow_test_report_{timestamp}.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return report_path


def main():
    """
    主测试函数
    """
    print("🧪 多智能体协作流程测试")
    print("=" * 50)
    
    # 创建测试查询
    test_query = create_test_query(TEST_CASE)
    print(f"📝 测试查询已生成 ({len(test_query)}字符)")
    
    # 模拟响应（在实际测试中，这里应该调用实际的MAS系统）
    print("\n⚠️  注意：这是一个测试框架")
    print("要进行实际测试，请：")
    print("1. 启动系统：python main.py")
    print("2. 在Web界面中提交测试查询")
    print("3. 记录完整的响应过程")
    print("4. 使用 analyze_workflow_response() 分析结果")
    
    print(f"\n📋 测试查询内容：")
    print("-" * 30)
    print(test_query)
    print("-" * 30)
    
    # 提供分析工具
    print("\n🔧 分析工具使用方法：")
    print("```python")
    print("# 将实际响应传入分析函数")
    print("response = '...'  # 从系统获取的完整响应")
    print("analysis = analyze_workflow_response(response)")
    print("report_path = save_test_results(analysis, response, TEST_CASE)")
    print("print(f'测试报告已保存到：{report_path}')")
    print("```")


if __name__ == "__main__":
    main()