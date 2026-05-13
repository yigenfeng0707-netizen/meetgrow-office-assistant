"""
MeetGrow AI Agent - 配置管理模块
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentConfig:
    """Agent 核心配置"""
    # API 配置
    api_base_url: str = field(
        default="https://api-inference.modelscope.cn/v1",
        metadata={"description": "模型 API 基础 URL"}
    )
    api_key: str = field(
        default="",
        metadata={"description": "ModelScope API Key"}
    )
    model_name: str = field(
        default="qwen3.6-35b-a3b",
        metadata={"description": "使用的模型名称"}
    )
    max_tokens: int = field(
        default=4096,
        metadata={"description": "最大生成长度"}
    )
    temperature: float = field(
        default=0.7,
        metadata={"description": "生成温度"}
    )

    # OCR 配置
    ocr_model_dir: str = field(
        default="models/paddleocr",
        metadata={"description": "PaddleOCR 模型目录"}
    )
    ocr_language: str = field(
        default="ch",
        metadata={"description": "OCR 语言 (ch=中英, en=英文, ja=日文)"}
    )

    # ASR 配置
    asr_model_dir: str = field(
        default="models/funasr",
        metadata={"description": "FunASR 模型目录"}
    )
    asr_sample_rate: int = field(
        default=16000,
        metadata={"description": "音频采样率 (Hz)"}
    )

    # TTS 配置
    tts_voice: str = field(
        default="zh-CN-XiaoxiaoNeural",
        metadata={"description": "TTS 声音 (zh-CN-XiaoxiaoNeural = 小晓, 女声)"}
    )
    tts_rate: str = field(
        default="+0%",
        metadata={"description": "语速 (+50% ~ -50%)"}
    )
    tts_volume: str = field(
        default="+0%",
        metadata={"description": "音量 (+100% ~ -100%)"}
    )

    # 工作目录
    workspace_dir: Path = field(
        default_factory=lambda: Path.home() / "meetgrow_data",
        metadata={"description": "工作数据目录"}
    )

    def __post_init__(self):
        """确保模型目录存在"""
        self.api_key = self.api_key or ""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)


# 全局配置实例
default_config = AgentConfig()


def get_config() -> AgentConfig:
    """获取当前配置"""
    return default_config
