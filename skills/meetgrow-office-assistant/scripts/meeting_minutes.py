#!/usr/bin/env python3
"""会议录音转纪要脚本"""
import json
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.asr_tool import ASRTool
from meetgrow_skill.tools.doc_tool import DocTool


def main():
    if len(sys.argv) < 2:
        print("用法: python meeting_minutes.py <会议录音路径> [会议标题]")
        sys.exit(1)

    audio_path = sys.argv[1]
    title = sys.argv[2] if len(sys.argv) > 2 else "未命名会议"

    config = get_config()

    # 1. 语音转文字
    asr = ASRTool(config)
    asr_result = asr.execute(audio_path=audio_path)
    if asr_result.get("status") != "success":
        print(json.dumps(asr_result, ensure_ascii=False, indent=2))
        sys.exit(1)

    transcript = asr_result.get("text", "")
    print(f"🎙️ 转写完成，字数: {len(transcript)}")

    # 2. 生成纪要
    doc = DocTool(config, task="minutes")
    minutes_result = doc.execute(
        transcript=transcript,
        meeting_title=title
    )
    if minutes_result.get("status") != "success":
        print(json.dumps(minutes_result, ensure_ascii=False, indent=2))
        sys.exit(1)
    minutes = minutes_result.get("minutes", "")

    output = {
        "status": "success",
        "audio_file": audio_path,
        "transcript": transcript,
        "minutes": minutes,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
