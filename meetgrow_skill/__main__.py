"""
MeetGrow AI Agent - CLI 命令行入口

用法:
    meetgrow init              初始化环境（下载模型等）
    meetgrow ocr <image>       OCR 识别图片
    meetgrow asr <audio>       语音转文字
    meetgrow tts <text>        文本转语音
    meetgrow agent "prompt"    Agent 交互
    meetgrow demo              运行演示
"""

import sys
import os
from pathlib import Path

# Ensure project root is in path when run as script
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import click
import logging
import json

try:
    from meetgrow_skill.config import AgentConfig, get_config
    from meetgrow_skill.core.agent import MeetGrowAgent
    from meetgrow_skill.core.memory import ConversationMemory
except ImportError:
    from config import AgentConfig, get_config
    from core.agent import MeetGrowAgent
    from core.memory import ConversationMemory
try:
    from meetgrow_skill.skill import SkillDefinition
except ImportError:
    from skill import SkillDefinition

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("meetgrow")


@click.group()
@click.option("--config", "-c", type=str, help="配置文件路径")
@click.pass_context
def main(ctx, config):
    """MeetGrow AI PC Agent Skill - 会展招商办公提效工具"""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config


@main.command()
@click.option("--workspace", "-w", type=str, default=None, help="工作目录")
@click.pass_context
def init(ctx, workspace):
    """初始化 MeetGrow 环境"""
    click.echo("🤖 MeetGrow AI PC Agent Skill - 初始化")
    click.echo("=" * 50)

    ws = Path(workspace) if workspace else Path.home() / "meetgrow_data"
    ws.mkdir(parents=True, exist_ok=True)

    # 创建必要的子目录
    for subdir in ["tts_output", "documents/archive", "models/paddleocr", "models/funasr"]:
        (ws / subdir).mkdir(parents=True, exist_ok=True)

    click.echo(f"✅ 工作目录: {ws}")

    # 创建配置文件
    config_file = ws / "config.yaml"
    if not config_file.exists():
        import yaml
        default_config = {
            "api_base_url": "https://api-inference.modelscope.cn/v1",
            "api_key": "",
            "model_name": "qwen3.6-35b-a3b",
            "ocr_language": "ch",
            "asr_sample_rate": 16000,
            "tts_voice": "zh-CN-XiaoxiaoNeural",
            "workspace_dir": str(ws),
        }
        config_file.write_text(yaml.dump(default_config, indent=2))
        click.echo(f"✅ 配置文件: {config_file}")
    else:
        click.echo(f"⚠️  配置文件已存在: {config_file}")

    # 创建 Skill 定义文件（供魔搭社区提交）
    skill_file = ws / "meetgrow_skill.json"
    skill = SkillDefinition()
    skill_data = {
        "metadata": {
            "name": skill.metadata.name,
            "version": skill.metadata.version,
            "title": skill.metadata.title,
            "description": skill.metadata.description,
            "author": skill.metadata.author,
            "tags": skill.metadata.tags,
        },
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in skill.tools
        ],
    }
    skill_file.write_text(
        json.dumps(skill_data, ensure_ascii=False, indent=2, default=str)
    )
    click.echo(f"✅ Skill 定义: {skill_file}")

    # 安装建议
    click.echo("")
    click.echo("📦 下一步: 安装依赖")
    click.echo("   pip install -r requirements.txt")
    click.echo("")
    click.echo("🔤 OCR: 需安装 paddlepaddle + paddleocr")
    click.echo("🎙️ ASR: 需安装 funasr + torchaudio")
    click.echo("🔊 TTS: 需安装 edge-tts (轻量)")
    click.echo("")
    click.echo("💡 提示: 设置 API Key")
    click.echo("   编辑配置文件或使用环境变量: MODELSCOPE_API_KEY=xxx")
    click.echo("")
    click.echo("✅ 初始化完成!")


@main.command()
@click.argument("image_path", type=str)
@click.pass_context
def ocr(ctx, image_path):
    """OCR 识别图片"""
    try:
        from meetgrow_skill.tools.ocr_tool import OCRTool
    except ImportError:
        click.echo("❌ 错误: 无法导入 OCR 模块。请安装 paddlepaddle paddleocr。", err=True)
        return

    config = get_config()
    ocr = OCRTool(config, task="general")

    click.echo(f"🔍 OCR 识别: {image_path}")
    result = ocr.execute(image_path=image_path)

    if result.get("status") == "success":
        click.echo(f"\n📄 识别文本:")
        click.echo(result.get("text", "无内容"))
        if result.get("processed"):
            click.echo(f"\n📋 结构化信息:")
            click.echo(json.dumps(result["processed"], ensure_ascii=False, indent=2))
    else:
        click.echo(f"❌ 错误: {result.get('error', '未知错误')}", err=True)


@main.command()
@click.argument("audio_path", type=str)
@click.pass_context
def asr(ctx, audio_path):
    """语音转文字"""
    from meetgrow_skill.tools.asr_tool import ASRTool

    config = get_config()
    asr = ASRTool(config)

    click.echo(f"🎙️ 语音识别: {audio_path}")
    result = asr.execute(audio_path=audio_path)

    if result.get("status") == "success":
        click.echo(f"\n📝 转写结果:")
        click.echo(result.get("text", "无内容"))
        click.echo(f"\n📊 字数: {result.get('word_count', 0)}")
    else:
        click.echo(f"❌ 错误: {result.get('error', '未知错误')}", err=True)


@main.command()
@click.argument("text", type=str)
@click.option("--voice", "-v", type=str, default="小晓", help="声音: 小晓/云扬/晓意/晓辰")
@click.option("--rate", "-r", type=str, default="+0%", help="语速: +10% / -10%")
@click.option("--output", "-o", type=str, default=None, help="输出文件路径")
@click.pass_context
def tts(ctx, text, voice, rate, output):
    """文本转语音"""
    from meetgrow_skill.tools.tts_tool import TTSTool

    config = get_config()
    tts = TTSTool(config)

    click.echo(f"🔊 TTS 合成: voice={voice}, rate={rate}")
    click.echo(f"   文本: {text[:50]}..." if len(text) > 50 else f"   文本: {text}")

    result = tts.execute(text=text, voice=voice, rate=rate, output_path=output)

    if result.get("status") == "success":
        click.echo(f"\n✅ 语音已生成: {result.get('audio_path')}")
        click.echo(f"   大小: {result.get('file_size_bytes', 0)} bytes")
    else:
        click.echo(f"❌ 错误: {result.get('error', '未知错误')}", err=True)


@main.command("agent")
@click.argument("prompt", type=str)
@click.option("--image", "-i", multiple=True, help="附加图片路径")
@click.option("--audio", "-a", multiple=True, help="附加音频路径")
@click.pass_context
def agent_cmd(ctx, prompt, image, audio):
    """Agent 交互 - 智能办公助手"""
    agent = MeetGrowAgent()

    click.echo(f"🤖 MeetGrow AI Agent")
    click.echo("-" * 50)
    click.echo(f"📝 用户: {prompt}")
    if image:
        click.echo(f"📎 图片: {', '.join(image)}")
    if audio:
        click.echo(f"🎙️ 音频: {', '.join(audio)}")
    click.echo("-" * 50)
    click.echo(f"🤖 Agent:")

    try:
        result = agent.process(
            user_input=prompt,
            images=list(image) if image else None,
            audio_files=list(audio) if audio else None
        )
        click.echo(result)
    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)


@main.command("demo")
@click.pass_context
def demo(ctx):
    """运行演示"""
    click.echo("🎬 MeetGrow AI PC Agent Skill - 演示")
    click.echo("=" * 50)

    # 演示 1: Skill 元数据
    try:
        from meetgrow_skill.skill import SkillDefinition
    except ImportError:
        from skill import SkillDefinition
    skill = SkillDefinition()
    click.echo(f"\n📋 Skill: {skill.metadata.title} v{skill.metadata.version}")
    click.echo(f"   描述: {skill.metadata.description}")
    click.echo(f"   工具数: {len(skill.tools)}")
    click.echo(f"   标签: {', '.join(skill.metadata.tags)}")

    # 演示 2: 工具列表
    click.echo(f"\n🔧 可用工具:")
    for tool in skill.tools:
        click.echo(f"   • {tool.name}")
        click.echo(f"     {tool.description[:80]}...")

    # 演示 3: TTS 演示（如果安装的话）
    click.echo(f"\n🔊 TTS 演示:")
    try:
        from meetgrow_skill.tools.tts_tool import TTSTool
        config = get_config()
        tts = TTSTool(config)
        result = tts.execute(
            text="你好！这是 MeetGrow AI PC Agent Skill 的演示。",
            voice="小晓",
            output=str(Path.home() / "meetgrow_data" / "demo_tts.mp3")
        )
        if result.get("status") == "success":
            click.echo(f"   ✅ 语音已生成: {result['audio_path']}")
        else:
            click.echo(f"   ⚠️  TTS 初始化失败: {result.get('error')}")
    except Exception as e:
        click.echo(f"   ⚠️  TTS 演示跳过: {e}")

    # 演示 4: 架构说明
    click.echo(f"\n🏗️ 架构:")
    click.echo("   Agent Brain: Qwen3.6-35B-A3B (API)")
    click.echo("   Local Tools: PaddleOCR + FunASR + edge-tts")
    click.echo("   Hardware: Intel Core Ultra 5 125H (CPU + Arc + NPU)")

    click.echo(f"\n✅ 演示完成!")


if __name__ == "__main__":
    main()
