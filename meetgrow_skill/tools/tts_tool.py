"""
MeetGrow AI Agent - TTS 语音合成模块
基于 edge-tts 实现中文语音合成
"""

import asyncio
import logging
from pathlib import Path

from ..config import AgentConfig
from .base import BaseTool

logger = logging.getLogger(__name__)


class TTSTool(BaseTool):
    """TTS 工具 - 文本转语音

    使用 edge-tts（微软 Edge 浏览器免费 TTS 引擎）。
    支持多种中文声音和语速/音调调节。
    """

    # 预定义声音
    VOICES = {
        "小晓": "zh-CN-XiaoxiaoNeural",       # 温柔女声（默认）
        "云扬": "zh-CN-YunyangNeural",         # 男声
        "晓晓": "zh-CN-XiaoxiaoMultilingualNeural",  # 多语言女声
        "晓意": "zh-CN-XiaoyiNeural",          # 活泼女声
        "晓辰": "zh-CN-YunxiNeural",           # 年轻男声
        "晓风": "zh-CN-YunfengNeural",         # 沉稳男声
    }

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self._output_dir = config.workspace_dir / "tts_output"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_voice(self, voice_name: str = None) -> str:
        """解析声音名称"""
        if voice_name is None:
            return self.config.tts_voice

        # 支持别名
        alias_map = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",
            "yunyang": "zh-CN-YunyangNeural",
            "xiaoyi": "zh-CN-XiaoyiNeural",
            "xiaochen": "zh-CN-YunxiNeural",
        }

        if voice_name.lower() in alias_map:
            return alias_map[voice_name.lower()]

        # 在预定义声音中查找
        for key, value in self.VOICES.items():
            if key == voice_name or value.lower() == voice_name.lower():
                return value

        return voice_name  # 直接返回，信任用户输入

    def execute(self, text: str, voice: str = None,
                rate: str = None, output_path: str = None,
                **kwargs) -> dict:
        """执行语音合成

        Args:
            text: 要转换的文本
            voice: 声音名称
            rate: 语速 (如 "+10%", "-5%")
            output_path: 输出文件路径（可选）
            **kwargs: 额外参数

        Returns:
            TTS 结果（包含输出文件路径）
        """
        if not text or not text.strip():
            return {"status": "error", "error": "输入文本为空"}

        # 解决声音
        resolved_voice = self._resolve_voice(voice)
        if rate is None:
            rate = self.config.tts_rate

        # 生成输出路径
        if output_path is None:
            import time
            filename = f"tts_{int(time.time())}.mp3"
            output_path = str(self._output_dir / filename)

        logger.info(f"🔊 TTS 合成: voice={resolved_voice}, rate={rate}, text_len={len(text)}")

        try:
            result = asyncio.run(
                self._synthesize(text, resolved_voice, rate, output_path)
            )

            if not Path(output_path).exists():
                return {"status": "error", "error": "TTS 输出文件未生成"}

            file_size = Path(output_path).stat().st_size
            return {
                "status": "success",
                "audio_path": output_path,
                "text": text,
                "voice": resolved_voice,
                "rate": rate,
                "file_size_bytes": file_size,
                "text_length": len(text),
            }

        except Exception as e:
            logger.error(f"TTS 执行失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _synthesize(self, text: str, voice: str,
                          rate: str, output_path: str):
        """异步执行 TTS 合成"""
        import edge_tts

        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
        )
        await communicate.save(output_path)

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": "text_to_speech",
                "description": "将文本转换为语音播报",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "需要转换的文本内容"
                        },
                        "voice": {
                            "type": "string",
                            "description": "声音: 小晓(女声默认)/云扬(男声)/晓意(活泼女声)/晓辰(年轻男声)",
                            "enum": list(self.VOICES.keys())
                        },
                        "rate": {
                            "type": "string",
                            "description": "语速调整",
                            "default": "+0%"
                        },
                        "output_path": {
                            "type": "string",
                            "description": "输出文件路径（可选）"
                        }
                    },
                    "required": ["text"]
                }
            }
        }
