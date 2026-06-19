#!/usr/bin/env python3
"""名片 OCR 识别脚本"""
import json
import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.ocr_tool import OCRTool


def main():
    if len(sys.argv) < 2:
        print("用法: python card_ocr.py <名片图片路径>")
        sys.exit(1)

    image_path = sys.argv[1]
    config = get_config()
    ocr = OCRTool(config, task="business_card")
    result = ocr.execute(image_path=image_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
