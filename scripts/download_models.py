#!/usr/bin/env python3
"""
MeetGrow AI PC Agent Skill - 本地模型下载脚本

自动下载 OCR / ASR 所需的本地模型权重：
- PaddleOCR: 首次调用时自动下载到 ~/.paddlex/
- FunASR: 从 ModelScope 下载 paraformer-zh / fsmn-vad / ct-punc

用法:
    python scripts/download_models.py              # 下载所有模型
    python scripts/download_models.py --asr-only   # 仅下载 ASR 模型
    python scripts/download_models.py --model-dir models/funasr
"""

import argparse
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("download_models")


ASR_MODELS = {
    "paraformer-zh": "iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
    "fsmn-vad": "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
    "ct-punc": "iic/punc_ct-transformer_cn-en-common-vocab471067-large",
}


def download_asr_models(model_dir: Path) -> bool:
    """使用 FunASR AutoModel 从 ModelScope 下载 ASR 模型"""
    try:
        from funasr import AutoModel
    except ImportError:
        logger.error("❌ 未安装 funasr，请先运行: pip install funasr")
        return False

    model_dir.mkdir(parents=True, exist_ok=True)
    success = True

    for name, model_id in ASR_MODELS.items():
        target = model_dir / name
        target.mkdir(parents=True, exist_ok=True)
        logger.info(f"🎙️ 下载 ASR 模型: {name} ({model_id})")
        try:
            # FunASR 通过 model 参数从 ModelScope 下载到本地缓存
            _ = AutoModel(model=model_id, model_revision="v2.0.4")
            logger.info(f"  ✅ {name} 下载完成")
        except Exception as e:
            logger.error(f"  ❌ {name} 下载失败: {e}")
            success = False

    return success


def ensure_ocr_models() -> bool:
    """PaddleOCR 模型在首次调用时自动下载，这里仅做环境检查"""
    try:
        from paddleocr import PaddleOCR
        logger.info("🔤 PaddleOCR 已安装，模型将在首次调用时自动下载")
        logger.info("  默认缓存路径: ~/.paddlex/ 或 ~/.paddleocr/")
        return True
    except ImportError:
        logger.warning("⚠️  PaddleOCR 未安装，请运行: pip install paddlepaddle paddleocr")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="下载 MeetGrow AI PC Agent Skill 本地模型"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models/funasr",
        help="ASR 模型下载目录 (默认: models/funasr)"
    )
    parser.add_argument(
        "--asr-only",
        action="store_true",
        help="仅下载 ASR 模型"
    )
    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="仅检查 OCR 环境"
    )

    args = parser.parse_args()
    model_dir = Path(args.model_dir).resolve()

    logger.info("=" * 60)
    logger.info("MeetGrow AI PC Agent Skill - 模型下载")
    logger.info("=" * 60)

    all_ok = True

    if args.ocr_only:
        all_ok = ensure_ocr_models()
    elif args.asr_only:
        all_ok = download_asr_models(model_dir)
    else:
        ocr_ok = ensure_ocr_models()
        asr_ok = download_asr_models(model_dir)
        all_ok = ocr_ok and asr_ok

    logger.info("=" * 60)
    if all_ok:
        logger.info("✅ 模型准备完成")
    else:
        logger.warning("⚠️  部分模型准备失败，请检查日志")
        sys.exit(1)


if __name__ == "__main__":
    main()
