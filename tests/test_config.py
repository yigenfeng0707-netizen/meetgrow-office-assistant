"""
MeetGrow AI Agent - 配置管理测试
"""

import sys
from pathlib import Path
import unittest
import tempfile


class TestAgentConfig(unittest.TestCase):
    """AgentConfig 单元测试"""

    def test_default_config(self):
        """测试默认配置值"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig()

        self.assertEqual(config.api_base_url, "https://api-inference.modelscope.cn/v1")
        self.assertEqual(config.api_key, "")
        self.assertEqual(config.model_name, "qwen3.6-35b-a3b")
        self.assertEqual(config.max_tokens, 4096)
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.ocr_language, "ch")
        self.assertEqual(config.asr_model_dir, "models/funasr")
        self.assertEqual(config.asr_sample_rate, 16000)
        self.assertEqual(config.tts_voice, "zh-CN-XiaoxiaoNeural")
        self.assertEqual(config.tts_rate, "+0%")
        self.assertEqual(config.tts_volume, "+0%")

    def test_custom_config(self):
        """测试自定义配置"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig(
            api_key="test-key-123",
            model_name="gpt-4",
            max_tokens=8192,
            temperature=0.3,
            api_base_url="https://custom.api/v1"
        )

        self.assertEqual(config.api_key, "test-key-123")
        self.assertEqual(config.model_name, "gpt-4")
        self.assertEqual(config.max_tokens, 8192)
        self.assertEqual(config.temperature, 0.3)
        self.assertEqual(config.api_base_url, "https://custom.api/v1")

    def test_workspace_dir_created(self):
        """测试工作目录自动创建"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig()
        # workspace_dir 应该存在
        self.assertTrue(config.workspace_dir.exists())

    def test_api_key_fallback(self):
        """测试 api_key 空值回退"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig(api_key=None)
        self.assertEqual(config.api_key, "")

    def test_ocr_languages(self):
        """测试不同 OCR 语言配置"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig(ocr_language="en")
        self.assertEqual(config.ocr_language, "en")

        config = AgentConfig(ocr_language="ja")
        self.assertEqual(config.ocr_language, "ja")

    def test_asr_sample_rate(self):
        """测试 ASR 采样率配置"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig(asr_sample_rate=8000)
        self.assertEqual(config.asr_sample_rate, 8000)

        config = AgentConfig(asr_sample_rate=44100)
        self.assertEqual(config.asr_sample_rate, 44100)

    def test_default_config_instance(self):
        """测试全局 default_config"""
        from meetgrow_skill.config import default_config
        self.assertIsNotNone(default_config)
        self.assertIsInstance(default_config, object)


class TestGetConfig(unittest.TestCase):
    """get_config 函数测试"""

    def test_returns_instance(self):
        """测试 get_config 返回配置实例"""
        from meetgrow_skill.config import get_config
        config = get_config()
        self.assertIsNotNone(config)
        # 返回的是同一个实例（单例模式）
        config2 = get_config()
        self.assertIs(config, config2)


if __name__ == "__main__":
    unittest.main()
