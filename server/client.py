#!/usr/bin/env python3
"""
MeetGrow AI PC Agent Skill - 服务客户端

用于调用本地常驻服务 server/server.py 提供的 OCR / ASR / TTS API。

用法:
    python server/client.py ocr examples/test_card.jpg
    python server/client.py asr meeting_recording.wav
    python server/client.py tts "会议提醒" --voice 小晓
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("❌ 缺少 requests。请运行: pip install requests")
    sys.exit(1)


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


def call_ocr(base_url: str, image_path: str, task: str = "general"):
    url = f"{base_url}/ocr"
    payload = {"image_path": image_path, "task": task}
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def call_asr(base_url: str, audio_path: str, diarization: bool = False):
    url = f"{base_url}/asr"
    payload = {"audio_path": audio_path, "diarization": diarization}
    response = requests.post(url, json=payload, timeout=300)
    response.raise_for_status()
    return response.json()


def call_tts(base_url: str, text: str, voice: str = "小晓", rate: str = "+0%"):
    url = f"{base_url}/tts"
    payload = {"text": text, "voice": voice, "rate": rate}
    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="MeetGrow Office Assistant 客户端")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="服务地址")
    parser.add_argument("--task", default="general", help="OCR 任务类型")
    parser.add_argument("--voice", default="小晓", help="TTS 声音")
    parser.add_argument("--rate", default="+0%", help="TTS 语速")
    parser.add_argument("command", choices=["ocr", "asr", "tts"], help="调用命令")
    parser.add_argument("input", help="输入文件路径或文本")

    args = parser.parse_args()

    try:
        if args.command == "ocr":
            result = call_ocr(args.base_url, args.input, args.task)
        elif args.command == "asr":
            result = call_asr(args.base_url, args.input)
        elif args.command == "tts":
            result = call_tts(args.base_url, args.input, args.voice, args.rate)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(result, ensure_ascii=False, indent=2))
    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务: {args.base_url}")
        print("   请先启动服务: python server/server.py")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ 请求失败: {e}")
        try:
            print(json.dumps(e.response.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(e.response.text)
        sys.exit(1)


if __name__ == "__main__":
    main()
