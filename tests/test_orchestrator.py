"""
MeetGrow AI Agent - 编排器测试
"""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import AgentConfig
from meetgrow_skill.core.orchestrator import ToolOrchestrator


class TestToolOrchestrator(unittest.TestCase):
    """工具编排器单元测试"""

    def setUp(self):
        self.config = AgentConfig()
        self.orchestrator = ToolOrchestrator(self.config)

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.orchestrator._tools)
        self.assertGreater(len(self.orchestrator._tools), 0)

    def test_execute_unknown_tool(self):
        """测试执行未知工具"""
        result = self.orchestrator.execute("unknown_tool", {"arg": "value"})
        self.assertEqual(result["status"], "error")
        self.assertIn("未知工具", result["error"])

    def test_register_tools(self):
        """测试工具注册"""
        expected_tools = [
            "ocr_business_card",
            "ocr_document",
            "speech_to_text",
            "text_to_speech",
            "generate_meeting_minutes",
            "smart_archive",
        ]
        for tool_name in expected_tools:
            self.assertIn(tool_name, self.orchestrator._tools)

    def test_execute_chain(self):
        """测试链式执行"""
        # 链式执行未知工具，应该终止并返回错误
        chain = [
            ("unknown1", {}),
            ("unknown2", {}),
        ]
        results = self.orchestrator.execute_chain(chain)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["status"], "error")

    def test_get_status(self):
        """测试状态查询"""
        status = self.orchestrator.get_status()
        self.assertIn("registered_tools", status)
        self.assertIn("execution_count", status)
        self.assertIn("recent_logs", status)
        self.assertGreater(len(status["registered_tools"]), 0)


if __name__ == "__main__":
    unittest.main()
