"""
基础使用示例

演示如何使用基于OxyGent的AI作文评审小组
"""

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from oxygent import MAS, oxy, Config
from oxygent.utils.env_utils import get_env_var

# 确保环境变量加载
load_dotenv()

# 设置OxyGent配置
Config.set_agent_llm_model("default_llm")

# 定义简化的OxyGent空间用于演示
demo_oxy_space = [
    # LLM配置
    oxy.HttpLLM(  # type: ignore
        name="default_llm",
        api_key=get_env_var("DEFAULT_LLM_API_KEY"),
        base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
        model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.7},
        semaphore=2,
        timeout=120,
    ),
    
    # 文本分析师 - 使用ChatAgent
    oxy.ChatAgent(  # type: ignore
        name="text_analyst",
        desc="文本分析师，负责分析作文的各个维度",
        prompt="""你是一位严谨的文本分析师，请客观分析作文的以下方面：
1. 基础规范：字数、段落、错误
2. 内容结构：主题、逻辑、完整性
3. 语言亮点：优美表达、修辞手法
4. 改进建议：可以提升的地方

请以结构化的方式输出分析结果。""",
    ),
    
    # 赞美鼓励师 - 使用ChatAgent
    oxy.ChatAgent(  # type: ignore
        name="praiser",
        desc="赞美鼓励师，专门发现和表扬学生作文的亮点",
        prompt="""你是充满热情的"阳光老师"，专门发现学生作文的亮点：
- 用具体的例子进行表扬
- 语气温暖鼓励，充满正能量
- 重点表扬优美的表达和用心的地方
- 让学生感受到写作的快乐

请生成温暖具体的表扬内容。""",
    ),
    
    # 启发引导师 - 使用ChatAgent  
    oxy.ChatAgent(  # type: ignore
        name="guide",
        desc="启发引导师，通过提问引导学生思考改进方向",
        prompt="""你是温和的"启发引导师"，通过问题引导学生思考：
- 不直接指出错误，而是用问题启发
- 引导学生自己发现可以改进的地方
- 提供思考的方向和角度
- 语气温和，给学生思考的空间

请设计启发性的问题和建议。""",
    ),
    
    # 主控智能体 - 使用ReActAgent
    oxy.ReActAgent(
        name="master_agent",
        desc="AI作文评审小组的主控智能体，协调各专业智能体完成作文评价",
        prompt="""你是AI作文评审小组的主控智能体。

当用户提交作文时，你需要：
1. 先调用text_analyst分析作文
2. 然后调用praiser生成表扬内容  
3. 接着调用guide生成启发建议
4. 最后整合所有结果生成综合评价报告

请按照这个流程协调各个智能体工作。""",
        is_master=True,
        sub_agents=["text_analyst", "praiser", "guide"],
        llm_model="default_llm",
        max_react_rounds=5,
    ),
]


async def demo_basic_usage():
    """基础使用演示"""
    print("🚀 启动AI作文评审小组演示...")
    
    # 示例作文
    sample_essay = """
我的妈妈

我的妈妈是一位温柔的老师。她有一双明亮的眼睛，就像天空中闪烁的星星。每天早上，妈妈都会为我准备美味的早餐，还会温柔地叫我起床。

妈妈工作很忙，但她总是抽时间陪我做作业。当我遇到不会的题目时，妈妈会耐心地教我，从不发脾气。她的笑容像春天的花朵一样美丽，总是让我感到温暖。

我爱我的妈妈，她是世界上最好的妈妈。我要好好学习，长大后像妈妈一样帮助别人。
    """.strip()
    
    try:
        async with MAS(oxy_space=demo_oxy_space) as mas:
            print("✅ OxyGent MAS系统启动成功")
            
            # 显示系统信息
            mas.show_mas_info()
            
            # 模拟作文评价流程
            print("\n📝 开始评价示例作文...")
            print(f"作文内容：\n{sample_essay}\n")
            
            # 调用主控智能体处理作文
            result = await mas.call(
                callee="master_agent",
                arguments={
                    "query": f"请评价以下小学生作文：\n\n{sample_essay}"
                }
            )
            
            print("📊 评价结果：")
            print(result)
            
            # 也可以单独调用各个智能体
            print("\n🔍 单独调用文本分析师...")
            analysis_result = await mas.call(
                callee="text_analyst", 
                arguments={"query": f"请分析这篇作文：\n{sample_essay}"}
            )
            print(f"分析结果：{analysis_result}")
            
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")


async def demo_interactive_chat():
    """交互式对话演示"""
    print("🗣️ 启动交互式对话模式...")
    
    try:
        async with MAS(oxy_space=demo_oxy_space) as mas:
            print("✅ 系统就绪，可以开始对话")
            
            # 启动Web服务进行交互
            await mas.start_web_service(
                first_query="你好！我是AI作文评审小组。请提交你的作文，或者告诉我你的教学需求。"
            )
            
    except KeyboardInterrupt:
        print("\n👋 用户主动退出")
    except Exception as e:
        print(f"❌ 交互过程中出现错误: {e}")


async def demo_batch_processing():
    """批量处理演示"""
    print("📚 批量处理演示...")
    
    # 多篇示例作文
    sample_essays = [
        {
            "title": "我的学校",
            "content": "我的学校很美丽。校园里有高大的梧桐树，还有漂亮的花坛。同学们在操场上快乐地玩耍，老师们认真地工作。我爱我的学校。"
        },
        {
            "title": "春天来了", 
            "content": "春天来了，小草从地下探出头来。柳树发芽了，像小姑娘的辫子在风中飘舞。燕子从南方飞回来了，在天空中自由地飞翔。春天真美啊！"
        },
        {
            "title": "我的好朋友",
            "content": "我有一个好朋友叫小明。他很聪明，学习成绩很好。他也很善良，总是帮助同学。我们经常一起玩游戏，一起学习。友谊让我们都很快乐。"
        }
    ]
    
    try:
        async with MAS(oxy_space=demo_oxy_space) as mas:
            print(f"📝 开始批量处理 {len(sample_essays)} 篇作文...")
            
            for i, essay in enumerate(sample_essays, 1):
                print(f"\n--- 处理第 {i} 篇作文：{essay['title']} ---")
                
                result = await mas.call(
                    callee="master_agent",
                    arguments={
                        "query": f"请评价作文《{essay['title']}》：\n\n{essay['content']}"
                    }
                )
                
                print(f"✅ 评价完成")
                # 可以在这里保存结果到文件
                
            print(f"\n🎉 批量处理完成！共处理 {len(sample_essays)} 篇作文")
            
    except Exception as e:
        print(f"❌ 批量处理过程中出现错误: {e}")


async def main():
    """主函数"""
    print("🎯 AI作文评审小组 - 基础使用示例")
    print("基于OxyGent多智能体框架构建")
    print("=" * 50)
    
    # 检查环境配置
    if not get_env_var("DEFAULT_LLM_API_KEY"):
        print("❌ 请先配置环境变量 DEFAULT_LLM_API_KEY")
        return
    
    while True:
        print("\n请选择演示模式：")
        print("1. 基础使用演示")
        print("2. 交互式对话模式") 
        print("3. 批量处理演示")
        print("4. 退出")
        
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == "1":
            await demo_basic_usage()
        elif choice == "2":
            await demo_interactive_chat()
        elif choice == "3":
            await demo_batch_processing()
        elif choice == "4":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    asyncio.run(main())