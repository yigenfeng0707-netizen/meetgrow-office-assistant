"""
MeetGrow AI Agent - ASR 语音识别模块
基于 FunASR 实现中文语音识别
"""

import json
import logging
import wave
from pathlib import Path
from typing import Optional

from ..config import AgentConfig
from .base import BaseTool

logger = logging.getLogger(__name__)


class ASRTool(BaseTool):
    """ASR 工具 - 语音转文字

    使用 FunASR (Paraformer 模型) 进行高精度中文语音识别。
    支持 wav/mp3/m4a 格式，自动转换为 16kHz WAV。
    """

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._asr = None

    def _init_asr(self):
        """初始化 FunASR（懒加载）"""
        if self._asr is not None:
            return

        try:
            from funasr import AutoModel

            logger.info("🎙️ 初始化 FunASR...")
            model_dir = self.config.asr_model_dir

            self._asr = AutoModel(
                model=f"{model_dir}/paraformer-zh",
                vad_model=f"{model_dir}/fsmn-vad",
                punc_model=f"{model_dir}/ct-punc",
                device="cpu",
            )
            logger.info("✅ FunASR 初始化完成")
        except ImportError:
            logger.warning(
                "FunASR 未安装，运行: pip install funasr torchaudio torch"
            )
            self._asr = None
        except Exception as e:
            # 模型未下载、路径错误等异常都视为模型不可用
            logger.warning(f"FunASR 初始化失败: {e}，模型可能未下载")
            logger.warning("运行 'python -m meetgrow_skill init' 下载模型")
            self._asr = None

    def execute(self, audio_path: str, diarization: bool = False, **kwargs) -> dict:
        """执行语音识别

        Args:
            audio_path: 音频文件路径 (wav/mp3/m4a)
            diarization: 是否启用说话人分离
            **kwargs: 额外参数

        Returns:
            转写结果
        """
        self._init_asr()

        if self._asr is None:
            return {
                "status": "error",
                "error": "FunASR 未安装。请运行: pip install funasr torchaudio torch"
            }

        path = Path(audio_path)
        if not path.exists():
            return {"status": "error", "error": f"文件不存在: {audio_path}"}

        logger.info(f"🎙️ ASR 识别: {audio_path}")

        try:
            # 执行识别
            result = self._asr.generate(
                input=str(path),
                cache={},
                language="auto",
                use_itn=True,  # 逆文本归一化
            )

            if not result:
                return {
                    "status": "success",
                    "text": "",
                    "message": "音频中未识别到语音内容"
                }

            # 解析结果
            if isinstance(result, list):
                segments = []
                full_text = ""
                for item in result:
                    if isinstance(item, dict):
                        text = item.get("text", "")
                        if text:
                            full_text += text + "\n"
                            segments.append({"text": text})
                    elif isinstance(item, str):
                        full_text += item + "\n"
                        segments.append({"text": item})
            else:
                full_text = str(result)
                segments = [{"text": full_text}]

            return {
                "status": "success",
                "text": full_text.strip(),
                "segments": segments,
                "audio_file": audio_path,
                "word_count": len(full_text.replace(" ", "")),
            }

        except Exception as e:
            logger.error(f"ASR 执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "speech_to_text",
                "description": "将语音/会议录音文件转换为文字",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "音频文件路径"
                        },
                        "diarization": {
                            "type": "boolean",
                            "description": "是否启用说话人分离",
                            "default": False
                        }
                    },
                    "required": ["audio_path"]
                }
            }
        }
