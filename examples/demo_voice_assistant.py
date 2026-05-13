"""
MeetGrow AI PC Agent Skill - 演示脚本
语音助手演示 - 展示 TTS 和 Agent 协作

用法:
    cd D:\meetgrow-agent-skill
    python examples/demo_voice_assistant.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.tts_tool import TTSTool


def main():
    print("=" * 60)
    print("🔊 MeetGrow AI - 语音助手演示")
    print("=" * 60)

    config = get_config()

    print("\n📋 语音助手能力:")
    print("   • 智能播报: 待办事项、会议提醒、新闻摘要")
    print("   • 多声音: 小晓(温柔女声)、云扬(沉稳男声)等")
    print("   • 语速调节: 支持加速/减速")
    print()

    # 测试 TTS
    print("🔊 测试语音合成...")
    tts = TTSTool(config)

    demo_texts = [
        ("小晓", "早上好！欢迎使用 MeetGrow 会展招商办公助手。"),
        ("云扬", "今天是您的工作会议日，请准备好相关材料。"),
        ("晓意", "好消息！华南区的展位已全部售罄！"),
    ]

    for voice_name, text in demo_texts:
        print(f"\n🎤 声音: {voice_name}")
        print(f"   文本: {text}")

        result = tts.execute(
            text=text,
            voice=voice_name,
            rate="+0%",
            output=str(config.workspace_dir / "tts_output" / f"demo_{voice_name}.mp3")
        )

        if result.get("status") == "success":
            print(f"   ✅ 已生成: {result['audio_path']} ({result['file_size_bytes']} bytes)")
        else:
            print(f"   ⚠️  生成失败: {result.get('error', '未知')}")

    print("\n✅ 演示完成!")


if __name__ == "__main__":
    main()
