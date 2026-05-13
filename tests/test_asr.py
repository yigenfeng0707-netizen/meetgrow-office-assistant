"""
MeetGrow AI Agent - ASR 工具测试
"""

import sys
import unittest
import tempfile
import wave
from unittest.mock import MagicMock, patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestASRTool(unittest.TestCase):
    """ASR 工具单元测试"""

    def setUp(self):
        """Mock FunASR，避免下载模型"""
        mock_auto_model = MagicMock()
        mock_funasr = MagicMock(AutoModel=mock_auto_model)
        self._patcher = unittest.mock.patch.dict(
            sys.modules, {"funasr": mock_funasr}
        )
        self._patcher.start()
        from meetgrow_skill.config import AgentConfig
        from meetgrow_skill.tools.asr_tool import ASRTool
        self.config = AgentConfig()
        self.asr = ASRTool(self.config)

    def tearDown(self):
        self._patcher.stop()

    # --- 初始化测试 ---

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.asr.config)
        self.assertIsNone(self.asr._asr)

    def test_get_schema(self):
        """测试获取工具 schema"""
        schema = self.asr.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "speech_to_text")
        self.assertIn("description", schema["function"])
        params = schema["function"]["parameters"]
        self.assertIn("properties", params)
        self.assertIn("audio_path", params["properties"])
        self.assertIn("required", params)

    # --- _init_asr 测试 ---

    def test_init_asr_lazy(self):
        """测试懒加载：首次调用才初始化"""
        self.assertIsNone(self.asr._asr)
        self.asr._init_asr()
        self.assertIsNotNone(self.asr._asr)
        # 再次调用不应重复初始化
        before = self.asr._asr
        self.asr._init_asr()
        self.assertIs(self.asr._asr, before)

    def test_init_asr_import_error(self):
        """测试 FunASR 导入失败"""
        self.asr._asr = None
        with unittest.mock.patch.dict(
            sys.modules, {"funasr": None}
        ):
            self.asr._init_asr()
        self.assertIsNone(self.asr._asr)

    def test_init_asr_model_error(self):
        """测试模型路径错误"""
        self.asr._asr = None
        mock_error_funasr = MagicMock()
        mock_error_funasr.AutoModel.side_effect = Exception("模型路径不存在")
        with unittest.mock.patch.dict(
            sys.modules, {"funasr": mock_error_funasr}
        ):
            self.asr._init_asr()
        self.assertIsNone(self.asr._asr)

    # --- 文件不存在测试 ---

    def test_file_not_found(self):
        """测试文件不存在时的错误处理"""
        result = self.asr.execute(audio_path="/nonexistent/path/audio.wav")
        self.assertEqual(result["status"], "error")
        self.assertIn("不存在", result["error"])

    def test_file_not_found_utf8(self):
        """测试文件不存在（中文路径）"""
        result = self.asr.execute(audio_path="/nonexistent/中文路径/测试.wav")
        self.assertEqual(result["status"], "error")
        self.assertIn("不存在", result["error"])

    # --- 辅助方法 ---

    def _create_mock_wav(self, filepath, duration_ms=1000):
        """创建一个最小的有效 WAV 文件用于测试"""
        with wave.open(filepath, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            nframes = duration_ms // 1000 * 16000
            wf.writeframes(b"\x00" * (nframes * 2))
        return filepath

    # --- 主执行路径测试 ---

    def test_execute_success_list_result(self):
        """测试成功识别，返回列表格式结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [
                {"text": "你好世界"},
                {"text": "这是测试"},
            ]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertIn("你好世界", result["text"])
            self.assertIn("这是测试", result["text"])
            self.assertEqual(len(result["segments"]), 2)
            self.assertIn("audio_file", result)
            self.assertIn("word_count", result)

    def test_execute_success_dict_result(self):
        """测试成功识别，返回 dict 格式结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = {"text": "hello world"}
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertIn("hello world", result["text"])

    def test_execute_success_string_result(self):
        """测试成功识别，返回字符串格式结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = "直接返回的文本"
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertIn("直接返回的文本", result["text"])

    def test_execute_empty_result(self):
        """测试空结果（无语音内容）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = None
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["text"], "")
            self.assertIn("未识别到语音", result["message"])

    def test_execute_empty_list_result(self):
        """测试空列表结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = []
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["text"], "")

    def test_execute_asr_error(self):
        """测试 ASR 执行时抛出异常"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.side_effect = Exception("识别超时")
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "error")
            self.assertIn("识别超时", result["error"])

    def test_execute_asr_none_state(self):
        """测试 _asr 为 None 时的行为（模型未初始化）"""
        self.asr._asr = None
        # Mock _init_asr to avoid running real init
        with unittest.mock.patch.object(
            self.asr, "_init_asr", return_value=None
        ):
            result = self.asr.execute(audio_path="test.wav")
        self.assertEqual(result["status"], "error")
        self.assertIn("FunASR 未安装", result["error"])

    def test_execute_with_diarization_param(self):
        """测试传入 diarization 参数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [{"text": "speaker 1: 你好"}]
            self.asr._asr = mock_asr

            result = self.asr.execute(
                audio_path=str(wav_path), diarization=True
            )
            self.assertEqual(result["status"], "success")
            self.assertIn("你好", result["text"])

    def test_execute_list_with_str_items(self):
        """测试列表中包含字符串类型元素"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [
                "第一句文本",
                {"text": "第二句文本"},
            ]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(result["status"], "success")
            self.assertIn("第一句文本", result["text"])
            self.assertIn("第二句文本", result["text"])

    def test_execute_segments_count(self):
        """测试 segments 数量正确"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [
                {"text": "段1"},
                {"text": "段2"},
                {"text": "段3"},
            ]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(len(result["segments"]), 3)

    def test_execute_word_count(self):
        """测试 word_count 计算"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [{"text": "测试"}]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            # word_count = len(full_text.replace(" ", "")), full_text has trailing \n
            self.assertEqual(result["word_count"], 3)

    def test_execute_text_stripped(self):
        """测试返回文本已去首尾空白"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [{"text": "  leading and trailing  "}]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            # text = full_text.strip() removes leading/trailing whitespace + \n
            self.assertEqual(result["text"], "leading and trailing")

    def test_execute_no_empty_text_segments(self):
        """测试空 text 的 segment 不加入结果"""
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "test.wav"
            self._create_mock_wav(str(wav_path))

            mock_asr = MagicMock()
            mock_asr.generate.return_value = [
                {"text": "有效文本"},
                {"text": ""},  # 空文本不应加入
            ]
            self.asr._asr = mock_asr

            result = self.asr.execute(audio_path=str(wav_path))
            self.assertEqual(len(result["segments"]), 1)


if __name__ == "__main__":
    unittest.main()
