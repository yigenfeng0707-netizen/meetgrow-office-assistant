#!/usr/bin/env python3
"""
MeetGrow AI PC Agent Skill - 常驻服务 (FastAPI)

推荐部署方式：
- 服务启动时一次性初始化所有本地工具（OCR/ASR/TTS）
- 客户端通过 HTTP API 调用，避免每次调用重新加载模型
- 适合集成到 MeetGrow AI 平台或其他业务系统

用法:
    python server/server.py              # 默认启动 http://127.0.0.1:8000
    python server/server.py --port 8080  # 指定端口
"""

import argparse
import logging
import sys
import uvicorn
from pathlib import Path

# 确保项目根目录在路径中
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError:
    print("❌ 缺少 fastapi / pydantic。请运行: pip install fastapi uvicorn")
    sys.exit(1)

from meetgrow_skill.config import AgentConfig, get_config
from meetgrow_skill.tools.ocr_tool import OCRTool
from meetgrow_skill.tools.asr_tool import ASRTool
from meetgrow_skill.tools.tts_tool import TTSTool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("meetgrow-server")

app = FastAPI(title="MeetGrow Office Assistant API")
config = get_config()

# 常驻工具实例（服务启动时懒加载，首次请求时初始化）
_tools = {
    "ocr": None,
    "asr": None,
    "tts": None,
}


def get_ocr() -> OCRTool:
    if _tools["ocr"] is None:
        _tools["ocr"] = OCRTool(config, task="general")
    return _tools["ocr"]


def get_asr() -> ASRTool:
    if _tools["asr"] is None:
        _tools["asr"] = ASRTool(config)
    return _tools["asr"]


def get_tts() -> TTSTool:
    if _tools["tts"] is None:
        _tools["tts"] = TTSTool(config)
    return _tools["tts"]


class OCRRequest(BaseModel):
    image_path: str = Field(..., description="图片文件路径")
    task: str = Field(default="general", description="识别任务: general / business_card")


class ASRRequest(BaseModel):
    audio_path: str = Field(..., description="音频文件路径")
    diarization: bool = Field(default=False, description="是否启用说话人分离")


class TTSRequest(BaseModel):
    text: str = Field(..., description="待合成文本")
    voice: str = Field(default="小晓", description="声音名称")
    rate: str = Field(default="+0%", description="语速调整")
    output_path: str = Field(default=None, description="输出文件路径（可选）")


@app.get("/")
def root():
    return {
        "name": "MeetGrow Office Assistant",
        "version": "1.0.0",
        "endpoints": ["/health", "/ocr", "/asr", "/tts"]
    }


@app.get("/health")
def health():
    return {"status": "ok", "tools": list(_tools.keys())}


@app.post("/ocr")
def ocr_endpoint(req: OCRRequest):
    tool = get_ocr()
    if req.task == "business_card":
        tool.task = "business_card"
    result = tool.execute(image_path=req.image_path)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "OCR 失败"))
    return result


@app.post("/asr")
def asr_endpoint(req: ASRRequest):
    tool = get_asr()
    result = tool.execute(audio_path=req.audio_path, diarization=req.diarization)
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "ASR 失败"))
    return result


@app.post("/tts")
def tts_endpoint(req: TTSRequest):
    tool = get_tts()
    result = tool.execute(
        text=req.text,
        voice=req.voice,
        rate=req.rate,
        output_path=req.output_path
    )
    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("error", "TTS 失败"))
    return result


def main():
    parser = argparse.ArgumentParser(description="MeetGrow Office Assistant 服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    args = parser.parse_args()

    logger.info(f"🚀 启动 MeetGrow Office Assistant 服务: http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
