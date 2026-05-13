"""
MeetGrow AI Agent - TTS 工具测试
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestTTSToolUnit(unittest.TestCase):
    """TTS 工具 单元测试"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig()

    def test_tts_schema(self):
        """测试 TTS 工具 Schema"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        schema = tts.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "text_to_speech")
        self.assertIn("text_to_speech", json.dumps(schema))

    def test_tts_properties(self):
        """测试 TTS 工具属性"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        self.assertIsNotNone(tts.VOICES)
        self.assertIn("小晓", tts.VOICES)

    def test_tts_execute_empty_text(self):
        """测试空文本输入"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        result = tts.execute(text="")
        self.assertEqual(result["status"], "error")

    def test_tts_execute_whitespace_text(self):
        """测试空白文本输入"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        result = tts.execute(text="   ")
        self.assertEqual(result["status"], "error")

    def test_tts_voices_keys(self):
        """测试语音列表完整性"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        expected_voices = {
            "小晓", "云扬", "晓晓", "晓意", "晓辰", "晓风"
        }
        self.assertEqual(set(tts.VOICES.keys()), expected_voices)

    def test_tts_voices_count(self):
        """测试语音数量"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        self.assertEqual(len(tts.VOICES), 6)

    def test_output_dir_created(self):
        """测试输出目录自动创建"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        self.assertTrue(tts._output_dir.exists())


class TestTTSToolMock(unittest.TestCase):
    """TTS 工具 Mock 测试 - Mock _synthesize 避免网络请求"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig()

    def test_synthesize_mock_success(self):
        """测试 TTS 合成成功（Mock _synthesize）"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)

        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(b'\x00' * 1024)
            temp_path = f.name

        try:
            with patch.object(tts, '_synthesize', return_value=None):
                result = tts.execute(
                    text="Hello test",
                    voice="小晓",
                    rate="+0%",
                    output_path=temp_path
                )
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["file_size_bytes"], 1024)
                self.assertEqual(result["text"], "Hello test")
                self.assertEqual(result["voice"], "zh-CN-XiaoxiaoNeural")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_synthesize_mock_empty_text(self):
        """测试 TTS 空文本（Mock 下确认错误处理）"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)

        result = tts.execute(text="")
        self.assertEqual(result["status"], "error")
        self.assertIn("空", result.get("error", ""))

    def test_synthesize_voice_aliases(self):
        """测试声音别名解析"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)

        self.assertEqual(
            tts._resolve_voice("xiaoxiao"),
            "zh-CN-XiaoxiaoNeural"
        )
        self.assertEqual(
            tts._resolve_voice("yunyang"),
            "zh-CN-YunyangNeural"
        )
        self.assertEqual(
            tts._resolve_voice("小晓"),
            "zh-CN-XiaoxiaoNeural"
        )
        self.assertEqual(
            tts._resolve_voice(None),
            self.config.tts_voice
        )

    def test_synthesize_rate_default(self):
        """测试默认语速设置"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        self.assertEqual(self.config.tts_rate, "+0%")

    def test_synthesize_mock_error_path(self):
        """测试合成成功但文件不存在（异常处理）"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)

        with patch.object(tts, '_synthesize', return_value=None):
            result = tts.execute(text="test", output_path=r"C:\nonexistent\output.mp3")
            self.assertEqual(result["status"], "error")
            self.assertIn("未生成", result.get("error", ""))


class TestTTSToolSchema(unittest.TestCase):
    """TTS 工具 Schema 完整性测试"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig()

    def test_schema_required_fields(self):
        """测试 Schema 必填字段"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        schema = tts.get_schema()
        self.assertIn("type", schema)
        self.assertIn("function", schema)
        self.assertIn("parameters", schema["function"])

    def test_schema_properties(self):
        """测试 Schema 属性定义"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        schema = tts.get_schema()
        props = schema["function"]["parameters"]["properties"]
        self.assertIn("text", props)
        self.assertIn("voice", props)
        self.assertIn("rate", props)
        self.assertIn("output_path", props)

    def test_schema_voice_enum(self):
        """测试 Schema voice 枚举"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tts = TTSTool(self.config)
        schema = tts.get_schema()
        voice_enum = schema["function"]["parameters"]["properties"]["voice"]["enum"]
        self.assertEqual(len(voice_enum), 6)


if __name__ == "__main__":
    unittest.main()
