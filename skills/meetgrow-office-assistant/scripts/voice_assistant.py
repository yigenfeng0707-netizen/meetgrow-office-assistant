#!/usr/bin/env python3
"""语音播报脚本"""
import json
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.tts_tool import TTSTool


def main():
    if len(sys.argv) < 2:
        print("用法: python voice_assistant.py <待播报文本> [--voice 小晓]")
        sys.exit(1)

    text = sys.argv[1]
    voice = "小晓"
    if "--voice" in sys.argv:
        idx = sys.argv.index("--voice")
        if idx + 1 < len(sys.argv):
            voice = sys.argv[idx + 1]

    config = get_config()
    tts = TTSTool(config)
    result = tts.execute(text=text, voice=voice)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
