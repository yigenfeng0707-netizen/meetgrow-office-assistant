"""
MeetGrow AI PC Agent Skill - 完整 Agent 演示
展示 Agent 大脑的多工具编排能力

用法:
    cd D:\meetgrow-agent-skill
    python examples/demo_complete_agent.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import AgentConfig
from meetgrow_skill.skill import SkillDefinition
from meetgrow_skill.core.orchestrator import ToolOrchestrator
from meetgrow_skill.core.memory import ConversationMemory


def main():
    print("=" * 60)
    print("🤖 MeetGrow AI PC Agent - 完整演示")
    print("=" * 60)

    # 1. 初始化配置
    config = AgentConfig()
    print(f"\n⚙️  配置:")
    print(f"   模型: {config.model_name}")
    print(f"   API:  {config.api_base_url}")
    print(f"   工作目录: {config.workspace_dir}")

    # 2. Skill 定义
    skill = SkillDefinition()
    print(f"\n📦 Skill: {skill.metadata.title}")
    print(f"   工具列表:")
    for tool in skill.tools:
        print(f"   • {tool.name}")
        print(f"     → {tool.description[:60]}...")

    # 3. 编排器
    orchestrator = ToolOrchestrator(config)
    print(f"\n🔄 工具编排器:")
    print(f"   已注册工具: {len(orchestrator._tools)}")

    # 4. 记忆系统
    memory = ConversationMemory(config.workspace_dir)
    print(f"\n🧠 记忆系统:")
    print(f"   会话: {memory._session_id}")

    # 5. 场景演示
    print("\n" + "=" * 60)
    print("🎬 场景演示")
    print("=" * 60)

    # 场景 1: 名片识别 + 自动建档
    print("\n📋 场景 1: 会展名片 OCR 识别 + 自动建档")
    print("-" * 50)
    print("用户: '扫描这张参会者名片，录入联系人系统'")
    print("Agent: 🔍 OCR 识别名片 → 📋 解析结构化信息 → 💾 归档到联系人")
    print("输出: 姓名、公司、职位、电话、邮箱 → JSON")

    # 场景 2: 会议录音 → 纪要
    print("\n📋 场景 2: 会议录音转纪要")
    print("-" * 50)
    print("用户: '整理这份会议录音，生成会议纪要'")
    print("Agent: 🎙️ ASR 转写 → 🤖 Agent 整理 → 📝 结构化纪要")
    print("输出: 议程、摘要、决策、待办 → Markdown")

    # 场景 3: 语音播报待办
    print("\n📋 场景 3: 语音播报今日待办")
    print("-" * 50)
    print("用户: '播报今天的工作待办'")
    print("Agent: 🤖 Agent 读取待办列表 → 🔊 TTS 语音播报")
    print("输出: mp3 语音文件")

    # 场景 4: 完整链式调度
    print("\n📋 场景 4: 链式调度 - 名片 OCR → TTS 播报")
    print("-" * 50)
    print("用户: '扫描这张名片并语音播报联系人信息'")
    print("Agent: 📄 OCR 名片 → 🔊 TTS 播报结果")
    print("链式: ocr_business_card → text_to_speech")

    # 6. 执行统计
    print("\n📊 当前执行统计:")
    status = orchestrator.get_status()
    print(f"   已注册工具: {len(status['registered_tools'])}")
    print(f"   执行次数: {status['execution_count']}")

    # 7. 总结
    print("\n" + "=" * 60)
    print("✅ 演示完成!")
    print("=" * 60)
    print("\n📦 安装依赖后运行实际示例:")
    print("   pip install -r requirements.txt")
    print("   meetgrow init")
    print("   meetgrow demo")
    print("   meetgrow ocr <image>")
    print("   meetgrow asr <audio>")
    print("   meetgrow tts <text>")
    print("   meetgrow agent <prompt>")


if __name__ == "__main__":
    main()
