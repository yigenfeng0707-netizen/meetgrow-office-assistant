"""
MeetGrow AI Agent - 工具基类测试
"""

import sys
from pathlib import Path
import unittest


class TestBaseTool(unittest.TestCase):
    """BaseTool 单元测试"""

    def test_base_tool_has_abstract_methods(self):
        """测试基类定义抽象方法"""
        from meetgrow_skill.tools.base import BaseTool
        # BaseTool 是抽象类，不能直接实例化
        with self.assertRaises(TypeError):
            BaseTool()

    def test_base_tool_inheritance(self):
        """测试工具继承基类"""
        from meetgrow_skill.tools.ocr_tool import OCRTool
        from meetgrow_skill.tools.base import BaseTool
        from meetgrow_skill.config import AgentConfig

        config = AgentConfig()
        ocr = OCRTool(config, task="general")
        self.assertIsInstance(ocr, BaseTool)

    def test_base_validate_path_not_exists(self):
        """测试路径验证 - 文件不存在"""
        from meetgrow_skill.tools.base import BaseTool
        from meetgrow_skill.config import AgentConfig
        from unittest.mock import MagicMock

        config = MagicMock(spec=AgentConfig)
        # 创建一个临时的实现
        class TestTool(BaseTool):
            def execute(self, **kwargs):
                return {"status": "success"}
            def get_schema(self):
                return {}

        tool = TestTool(config)
        result = tool.validate_path("/nonexistent/path/file.txt")
        self.assertEqual(result["status"], "error")
        self.assertIn("不存在", result["error"])


if __name__ == "__main__":
    unittest.main()
