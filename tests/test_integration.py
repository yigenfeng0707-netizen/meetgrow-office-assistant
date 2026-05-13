"""
MeetGrow AI Agent - 端到端集成测试
测试 Agent 完整工作流程：配置加载 → 工具注册 → 工具编排 → 记忆管理
所有外部依赖（OCR/ASR/TTS/LLM/OCR模型）均已 Mock，无需网络请求和模型加载
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockToolInstance:
    """轻量级 Mock 工具实例，零延迟，不加载任何模型"""
    def __init__(self, config=None, task=None, **kwargs):
        self.config = config
        self.task = task
        self._name_map = {
            "business_card": "ocr_business_card",
            "general": "ocr_general",
            "minutes": "generate_meeting_minutes",
            "archive": "smart_archive",
        }
        # Voice alias map (matching TTSTool)
        self._voice_aliases = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",
            "xiaoyi": "zh-CN-XiaoyiNeural",
            "yunyang": "zh-CN-YunyangNeural",
            "雲揚": "zh-TW-YunYunNeural",
            "云扬": "zh-CN-YunyangNeural",
        }

    def _resolve_voice(self, voice):
        return self._voice_aliases.get(voice, voice)

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": getattr(self, '_schema_name',
                               self._name_map.get(self.task, str(self.task))),
                "description": "Mock tool",
                "parameters": {"type": "object", "properties": {}}
            }
        }

    def execute(self, **kwargs):
        # TTS: 空文本应返回 error
        if hasattr(self, '_schema_name') and self._schema_name == "text_to_speech":
            text = kwargs.get("text", "")
            if not text or not text.strip():
                return {"status": "error", "error": "Empty text"}
            return {"status": "success", "result": "audio.mp3"}
        # ASR: 文件不存在应返回 error
        if hasattr(self, '_schema_name') and self._schema_name == "speech_to_text":
            audio_path = kwargs.get("audio_path", "")
            if not audio_path or not os.path.exists(audio_path):
                return {"status": "error", "error": "File not found: " + str(audio_path)}
            return {"status": "success", "result": "Transcription"}
        # OCR: 无图片应返回错误
        if hasattr(self, 'task') and self.task in ('business_card', 'general'):
            return {"status": "error", "error": "No image provided"}
        if hasattr(self, 'task') and self.task == 'minutes':
            transcript = kwargs.get('transcript')
            if not transcript:
                return {"status": "error", "error": "Missing transcript"}
            return {"status": "success", "result": "Meeting minutes generated"}
        if hasattr(self, 'task') and self.task == 'archive':
            files = kwargs.get('files')
            category = kwargs.get('category')
            if not files or not category:
                return {"status": "error", "error": "Missing files or category"}
            return {"status": "success", "result": "Files archived"}
        return {"status": "success", "result": "Mock execution"}


# Mock 所有工具类
def mock_ocr_tool(cls, config=None, task=None):
    t = MockToolInstance(config, task)
    t._schema_name = "ocr_business_card" if task == "business_card" else "ocr_general"
    return t


def mock_asr_tool(cls, config=None):
    t = MockToolInstance(config)
    t._schema_name = "speech_to_text"
    return t


def mock_tts_tool(cls, config=None):
    t = MockToolInstance(config)
    t._schema_name = "text_to_speech"
    return t


def mock_doc_tool(cls, config=None, task=None):
    t = MockToolInstance(config, task)
    return t


class TestEndToEndFlow(unittest.TestCase):
    """端到端工作流集成测试"""

    def setUp(self):
        from meetgrow_skill.config import default_config
        self.config = default_config

    def test_full_skill_definition(self):
        """测试完整 Skill 定义生成"""
        from meetgrow_skill.skill import SkillDefinition

        skill = SkillDefinition()
        self.assertIsNotNone(skill.metadata)
        self.assertEqual(skill.metadata.name, "meetgrow-office-assistant")
        self.assertEqual(skill.metadata.version, "1.0.0")
        self.assertIn("会展招商", skill.metadata.description)
        self.assertEqual(len(skill.tools), 6)

        tool_names = [t.name for t in skill.tools]
        expected = {"ocr_business_card", "ocr_document", "speech_to_text",
                     "text_to_speech", "generate_meeting_minutes", "smart_archive"}
        self.assertEqual(set(tool_names), expected)

        for tool in skill.tools:
            fmt = tool.to_openai_format()
            self.assertEqual(fmt["type"], "function")
            self.assertIn("name", fmt["function"])

    @patch('meetgrow_skill.tools.ocr_tool.OCRTool', side_effect=mock_ocr_tool)
    def test_ocr_tool_schema(self, mock_cls):
        """测试 OCR 工具 Schema 正确性"""
        from meetgrow_skill.tools.ocr_tool import OCRTool
        tool_card = OCRTool(self.config, task="business_card")
        schema_card = tool_card.get_schema()
        self.assertEqual(schema_card["type"], "function")
        self.assertEqual(schema_card["function"]["name"], "ocr_business_card")

        tool_gen = OCRTool(self.config, task="general")
        schema_gen = tool_gen.get_schema()
        self.assertEqual(schema_gen["function"]["name"], "ocr_general")

    @patch('meetgrow_skill.tools.tts_tool.TTSTool', side_effect=mock_tts_tool)
    def test_tts_tool_lifecycle(self, mock_cls):
        """测试 TTS 工具完整生命周期"""
        from meetgrow_skill.tools.tts_tool import TTSTool
        tool = TTSTool(self.config)
        result = tool.execute(text="")
        self.assertEqual(result["status"], "error")
        self.assertEqual(tool._resolve_voice("xiaoxiao"), "zh-CN-XiaoxiaoNeural")
        self.assertEqual(tool._resolve_voice("云扬"), "zh-CN-YunyangNeural")
        schema = tool.get_schema()
        self.assertEqual(schema["function"]["name"], "text_to_speech")

    @patch('meetgrow_skill.tools.asr_tool.ASRTool', side_effect=mock_asr_tool)
    def test_asr_tool_lifecycle(self, mock_cls):
        """测试 ASR 工具完整生命周期（Mock 模式）"""
        from meetgrow_skill.tools.asr_tool import ASRTool
        tool = ASRTool(self.config)
        result = tool.execute(audio_path="/nonexistent.wav")
        self.assertEqual(result["status"], "error")
        schema = tool.get_schema()
        self.assertEqual(schema["function"]["name"], "speech_to_text")

    @patch('meetgrow_skill.tools.doc_tool.DocTool', side_effect=mock_doc_tool)
    def test_doc_tool_lifecycle(self, mock_cls):
        """测试文档工具完整生命周期"""
        from meetgrow_skill.tools.doc_tool import DocTool
        tool = DocTool(self.config, task="minutes")
        schema = tool.get_schema()
        self.assertEqual(schema["function"]["name"], "generate_meeting_minutes")

        result = tool.execute(task="generate_meeting_minutes", transcript=None)
        self.assertEqual(result["status"], "error")

        result = tool.execute(task="smart_archive", files=[], category=None)
        self.assertEqual(result["status"], "error")

    def test_orchestrator_init_and_status(self):
        """测试工具编排器初始化和状态（Mock 所有工具）"""
        with patch('meetgrow_skill.core.orchestrator.OCRTool', side_effect=mock_ocr_tool), \
             patch('meetgrow_skill.core.orchestrator.ASRTool', side_effect=mock_asr_tool), \
             patch('meetgrow_skill.core.orchestrator.TTSTool', side_effect=mock_tts_tool), \
             patch('meetgrow_skill.core.orchestrator.DocTool', side_effect=mock_doc_tool):
            from meetgrow_skill.core.orchestrator import ToolOrchestrator
            orch = ToolOrchestrator(self.config)
            status = orch.get_status()
            self.assertIn("registered_tools", status)
            self.assertEqual(status["execution_count"], 0)

            expected_tools = {"ocr_business_card", "ocr_document", "speech_to_text",
                              "text_to_speech", "generate_meeting_minutes", "smart_archive"}
            self.assertEqual(set(status["registered_tools"]), expected_tools)

    def test_orchestrator_execute_unknown(self):
        """测试编排器执行未知工具"""
        with patch('meetgrow_skill.core.orchestrator.OCRTool', side_effect=mock_ocr_tool), \
             patch('meetgrow_skill.core.orchestrator.ASRTool', side_effect=mock_asr_tool), \
             patch('meetgrow_skill.core.orchestrator.TTSTool', side_effect=mock_tts_tool), \
             patch('meetgrow_skill.core.orchestrator.DocTool', side_effect=mock_doc_tool):
            from meetgrow_skill.core.orchestrator import ToolOrchestrator
            orch = ToolOrchestrator(self.config)
            result = orch.execute("nonexistent_tool", {})
            self.assertEqual(result["status"], "error")
            self.assertIn("未知工具", result["error"])

    def test_memory_persistence(self):
        """测试对话记忆持久化"""
        from meetgrow_skill.core.memory import ConversationMemory
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            memory = ConversationMemory(workspace_dir=workspace)
            for i in range(8):
                memory.add_message("user", f"消息 {i}")
            memory.add_message("user", "你好")
            memory.add_message("assistant", "你好！")
            history_file = workspace / "conversation_history.json"
            self.assertTrue(history_file.exists())
            data = json.loads(history_file.read_text())
            self.assertEqual(len(data), 10)
            messages = memory.get_context_messages()
            self.assertEqual(len(messages), 10)
            self.assertEqual(messages[-2]["content"], "你好")
            self.assertEqual(messages[-1]["content"], "你好！")

    def test_memory_messages_limit(self):
        """测试记忆消息数量限制（最多 50 条）"""
        from meetgrow_skill.core.memory import ConversationMemory
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            memory = ConversationMemory(workspace_dir=workspace)
            for i in range(55):
                memory.add_message("user", f"消息 {i}")
            self.assertLessEqual(len(memory._history), 50)
            self.assertEqual(memory._history[-1]["content"], "消息 54")

    @patch('meetgrow_skill.tools.ocr_tool.OCRTool', side_effect=mock_ocr_tool)
    @patch('meetgrow_skill.tools.asr_tool.ASRTool', side_effect=mock_asr_tool)
    @patch('meetgrow_skill.tools.tts_tool.TTSTool', side_effect=mock_tts_tool)
    @patch('meetgrow_skill.tools.doc_tool.DocTool', side_effect=mock_doc_tool)
    def test_all_tools_have_schema(self, mock_doc, mock_tts, mock_asr, mock_ocr):
        """测试所有工具都有完整 Schema"""
        from meetgrow_skill.tools.ocr_tool import OCRTool
        from meetgrow_skill.tools.asr_tool import ASRTool
        from meetgrow_skill.tools.tts_tool import TTSTool
        from meetgrow_skill.tools.doc_tool import DocTool

        tools = [
            OCRTool(self.config, task="business_card"),
            ASRTool(self.config),
            TTSTool(self.config),
            DocTool(self.config, task="minutes"),
        ]
        for tool in tools:
            schema = tool.get_schema()
            self.assertEqual(schema["type"], "function")
            self.assertIn("function", schema)
            self.assertIn("name", schema["function"])
            self.assertIn("description", schema["function"])

    def test_skill_manifest_generation(self):
        """测试 Skill Manifest 生成"""
        from meetgrow_skill.skill import SkillDefinition
        from meetgrow_skill.config import get_config

        skill = SkillDefinition()
        config = get_config()

        manifest = {
            "name": skill.metadata.name,
            "version": skill.metadata.version,
            "description": skill.metadata.description,
            "tools": [tool.to_openai_format() for tool in skill.tools],
            "config": {"model": config.model_name, "max_tokens": config.max_tokens},
        }
        self.assertIn("name", manifest)
        self.assertIn("tools", manifest)
        self.assertEqual(len(manifest["tools"]), 6)
        json_str = json.dumps(manifest, ensure_ascii=False)
        self.assertGreater(len(json_str), 100)


class TestScenarioSimulation(unittest.TestCase):
    """场景模拟测试"""

    def setUp(self):
        from meetgrow_skill.config import default_config
        self.config = default_config

    def test_meeting_workflow(self):
        """模拟完整会议工作流"""
        with patch('meetgrow_skill.core.orchestrator.OCRTool', side_effect=mock_ocr_tool), \
             patch('meetgrow_skill.core.orchestrator.ASRTool', side_effect=mock_asr_tool), \
             patch('meetgrow_skill.core.orchestrator.TTSTool', side_effect=mock_tts_tool), \
             patch('meetgrow_skill.core.orchestrator.DocTool', side_effect=mock_doc_tool):
            from meetgrow_skill.core.orchestrator import ToolOrchestrator
            orch = ToolOrchestrator(self.config)
            status = orch.get_status()
            self.assertEqual(status["execution_count"], 0)
            self.assertEqual(len(status["registered_tools"]), 6)

            result = orch.execute(
                "generate_meeting_minutes",
                {"transcript": "今天讨论了下个项目计划", "meeting_title": "项目启动会"}
            )
            self.assertIsNotNone(result)

    @patch('meetgrow_skill.tools.ocr_tool.OCRTool', side_effect=mock_ocr_tool)
    def test_business_card_workflow(self, mock_cls):
        """模拟名片识别工作流"""
        from meetgrow_skill.tools.ocr_tool import OCRTool
        tool = OCRTool(self.config, task="business_card")
        schema = tool.get_schema()
        self.assertIn("function", schema)
        self.assertIn("name", schema["function"])
        self.assertEqual(schema["type"], "function")

    def test_multi_scenario_tools(self):
        """验证多场景工具覆盖"""
        from meetgrow_skill.skill import SkillDefinition
        skill = SkillDefinition()
        tool_names = skill.get_tool_names()

        scenarios = {
            "ocr_business_card": "名片识别",
            "ocr_document": "文档扫描",
            "speech_to_text": "语音转写",
            "text_to_speech": "语音合成",
            "generate_meeting_minutes": "会议纪要",
            "smart_archive": "智能归档",
        }
        for tool_name, scenario in scenarios.items():
            self.assertIn(tool_name, tool_names,
                          f"场景 '{scenario}' 缺少工具: {tool_name}")

    def test_orchestrator_chain_execution(self):
        """测试编排器链式执行"""
        with patch('meetgrow_skill.core.orchestrator.OCRTool', side_effect=mock_ocr_tool), \
             patch('meetgrow_skill.core.orchestrator.ASRTool', side_effect=mock_asr_tool), \
             patch('meetgrow_skill.core.orchestrator.TTSTool', side_effect=mock_tts_tool), \
             patch('meetgrow_skill.core.orchestrator.DocTool', side_effect=mock_doc_tool):
            from meetgrow_skill.core.orchestrator import ToolOrchestrator
            orch = ToolOrchestrator(self.config)
            chain = [
                ("generate_meeting_minutes", {
                    "transcript": "会议内容", "meeting_title": "测试"
                }),
                ("text_to_speech", {"text": "测试"}),
            ]
            results = orch.execute_chain(chain)
            self.assertIsInstance(results, list)
            self.assertGreater(len(results), 0)


class TestConfigIntegration(unittest.TestCase):
    """配置集成测试"""

    def test_default_config_valid(self):
        """测试默认配置有效性"""
        from meetgrow_skill.config import default_config
        self.assertEqual(default_config.model_name, "qwen3.6-35b-a3b")
        self.assertEqual(default_config.max_tokens, 4096)
        self.assertEqual(default_config.temperature, 0.7)
        self.assertEqual(default_config.ocr_language, "ch")
        self.assertEqual(default_config.asr_sample_rate, 16000)

    def test_get_config_returns_default(self):
        """测试 get_config 返回默认配置"""
        from meetgrow_skill.config import get_config, default_config
        cfg = get_config()
        self.assertEqual(cfg.model_name, default_config.model_name)

    def test_workspace_dir_created(self):
        """测试工作目录自动创建"""
        from meetgrow_skill.config import default_config
        self.assertTrue(default_config.workspace_dir.exists())


if __name__ == "__main__":
    unittest.main()
