"""
MeetGrow AI Agent - Skill 定义测试
"""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSkillMetadata(unittest.TestCase):
    """SkillMetadata 单元测试"""

    def test_default_metadata(self):
        """测试默认元数据值"""
        from meetgrow_skill.skill import SkillMetadata
        meta = SkillMetadata()

        self.assertEqual(meta.name, "meetgrow-office-assistant")
        self.assertEqual(meta.version, "1.0.0")
        self.assertEqual(meta.title, "MeetGrow AI PC Agent Skill")
        self.assertEqual(meta.author, "WinClaw")
        self.assertEqual(meta.license, "MIT")
        self.assertIn("agent", meta.tags)
        self.assertIn("ocr", meta.tags)
        self.assertIn("intel-ai-pc", meta.tags)

    def test_custom_metadata(self):
        """测试自定义元数据"""
        from meetgrow_skill.skill import SkillMetadata
        meta = SkillMetadata(
            name="custom-skill",
            version="2.0.0",
            title="Custom Title",
            author="TestAuthor"
        )
        self.assertEqual(meta.name, "custom-skill")
        self.assertEqual(meta.version, "2.0.0")
        self.assertEqual(meta.title, "Custom Title")
        self.assertEqual(meta.author, "TestAuthor")


class TestToolDefinition(unittest.TestCase):
    """ToolDefinition 单元测试"""

    def test_to_openai_format(self):
        """测试转换为 OpenAI 格式"""
        from meetgrow_skill.skill import ToolDefinition
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            parameters={
                "type": "object",
                "properties": {"input": {"type": "string"}}
            },
            examples=[]
        )

        result = tool.to_openai_format()
        self.assertEqual(result["type"], "function")
        self.assertEqual(result["function"]["name"], "test_tool")
        self.assertEqual(result["function"]["description"], "A test tool")
        self.assertIn("parameters", result["function"])

    def test_tool_with_examples(self):
        """测试带示例的工具定义"""
        from meetgrow_skill.skill import ToolDefinition
        tool = ToolDefinition(
            name="ocr_test",
            description="OCR test",
            parameters={"type": "object", "properties": {}},
            examples=[
                {"input": {"path": "test.jpg"}, "output": {"text": "hello"}}
            ]
        )
        self.assertEqual(len(tool.examples), 1)
        self.assertEqual(tool.examples[0]["output"]["text"], "hello")


class TestSkillDefinition(unittest.TestCase):
    """SkillDefinition 完整测试"""

    def setUp(self):
        from meetgrow_skill.skill import SkillDefinition
        self.skill = SkillDefinition()

    def test_metadata(self):
        """测试 Skill 元数据"""
        self.assertEqual(self.skill.metadata.name, "meetgrow-office-assistant")
        self.assertEqual(self.skill.metadata.version, "1.0.0")
        self.assertGreater(len(self.skill.metadata.tags), 0)

    def test_tool_count(self):
        """测试工具数量"""
        self.assertEqual(len(self.skill.tools), 6)

    def test_tool_names(self):
        """测试获取所有工具名称"""
        names = self.skill.get_tool_names()
        self.assertEqual(len(names), 6)
        self.assertIn("ocr_business_card", names)
        self.assertIn("ocr_document", names)
        self.assertIn("speech_to_text", names)
        self.assertIn("text_to_speech", names)
        self.assertIn("generate_meeting_minutes", names)
        self.assertIn("smart_archive", names)

    def test_tool_descriptions(self):
        """测试获取工具描述"""
        descs = self.skill.get_tool_descriptions()
        self.assertEqual(len(descs), 6)
        for desc in descs:
            self.assertIn(":", desc)  # 格式: name: description

    def test_ocr_business_card_tool(self):
        """测试名片 OCR 工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        ocr = tools["ocr_business_card"]
        self.assertIn("名片", ocr.description)
        self.assertIn("image_path", ocr.parameters["properties"])
        self.assertIn("image_path", ocr.parameters["required"])
        self.assertEqual(len(ocr.examples), 1)

    def test_speech_to_text_tool(self):
        """测试语音转文字工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        asr = tools["speech_to_text"]
        self.assertIn("语音", asr.description)
        self.assertIn("audio_path", asr.parameters["properties"])
        self.assertIn("audio_path", asr.parameters["required"])

    def test_text_to_speech_tool(self):
        """测试语音合成工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        tts = tools["text_to_speech"]
        self.assertIn("语音", tts.description)
        self.assertIn("text", tts.parameters["properties"])
        self.assertIn("voice", tts.parameters["properties"])

    def test_all_tools_have_openai_format(self):
        """测试所有工具可转换为 OpenAI 格式"""
        for tool in self.skill.tools:
            result = tool.to_openai_format()
            self.assertEqual(result["type"], "function")
            self.assertIn("name", result["function"])
            self.assertIn("description", result["function"])
            self.assertIn("parameters", result["function"])

    def test_meeting_minutes_tool(self):
        """测试会议纪要工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        minutes = tools["generate_meeting_minutes"]
        self.assertIn("纪要", minutes.description)
        self.assertIn("transcript", minutes.parameters["required"])
        self.assertIn("meeting_title", minutes.parameters["required"])

    def test_smart_archive_tool(self):
        """测试智能归档工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        archive = tools["smart_archive"]
        self.assertIn("归档", archive.description)
        self.assertIn("files", archive.parameters["required"])
        self.assertIn("category", archive.parameters["required"])

    def test_ocr_document_tool(self):
        """测试文档 OCR 工具定义"""
        tools = {t.name: t for t in self.skill.tools}
        ocr_doc = tools["ocr_document"]
        self.assertIn("文档", ocr_doc.description)
        self.assertIn("task", ocr_doc.parameters["properties"])
        task_enum = ocr_doc.parameters["properties"]["task"].get("enum", [])
        self.assertIn("general", task_enum)
        self.assertIn("table", task_enum)
        self.assertIn("receipt", task_enum)


if __name__ == "__main__":
    unittest.main()
