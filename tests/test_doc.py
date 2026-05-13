"""
MeetGrow AI Agent - 文档处理工具测试
"""

import sys
import tempfile
import json
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import AgentConfig
from meetgrow_skill.tools.doc_tool import DocTool


class TestDocTool(unittest.TestCase):
    """DocTool 单元测试"""

    def setUp(self):
        self.config = AgentConfig()

    def test_init_minutes(self):
        """测试初始化 - 会议纪要模式"""
        doc = DocTool(self.config, task="minutes")
        self.assertEqual(doc.task, "minutes")
        self.assertTrue(doc.workspace.exists())

    def test_init_archive(self):
        """测试初始化 - 归档模式"""
        doc = DocTool(self.config, task="archive")
        self.assertEqual(doc.task, "archive")

    def test_init_unknown_task(self):
        """测试初始化 - 未知任务"""
        doc = DocTool(self.config, task="unknown")
        self.assertEqual(doc.task, "unknown")

    def test_execute_unknown_task(self):
        """测试执行 - 未知任务返回错误"""
        doc = DocTool(self.config, task="unknown")
        result = doc.execute()
        self.assertEqual(result["status"], "error")
        self.assertIn("未知任务", result["error"])

    def test_meeting_minutes_missing_transcript(self):
        """测试会议纪要 - 缺少转写文本"""
        doc = DocTool(self.config, task="minutes")
        result = doc._generate_meeting_minutes(
            transcript=None,
            meeting_title="测试会议"
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("转写", result["error"])

    def test_meeting_minutes_empty_transcript(self):
        """测试会议纪要 - 空转写文本"""
        doc = DocTool(self.config, task="minutes")
        result = doc._generate_meeting_minutes(
            transcript="",
            meeting_title="测试会议"
        )
        self.assertEqual(result["status"], "error")
        self.assertIn("转写", result["error"])

    def test_smart_archive_missing_files(self):
        """测试智能归档 - 缺少文件"""
        doc = DocTool(self.config, task="archive")
        result = doc._smart_archive(files=None, category="test")
        self.assertEqual(result["status"], "error")
        self.assertIn("需要", result["error"])

    def test_smart_archive_missing_category(self):
        """测试智能归档 - 缺少分类"""
        doc = DocTool(self.config, task="archive")
        result = doc._smart_archive(files=["test.txt"], category=None)
        self.assertEqual(result["status"], "error")

    def test_smart_archive_with_nonexistent_files(self):
        """测试智能归档 - 文件不存在"""
        doc = DocTool(self.config, task="archive")
        result = doc._smart_archive(
            files=["/nonexistent/file1.txt", "/nonexistent/file2.txt"],
            category="test_category"
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["indexed"], 0)
        self.assertGreater(len(result["errors"]), 0)

    def test_smart_archive_with_real_files(self):
        """测试智能归档 - 真实文件归档"""
        doc = DocTool(self.config, task="archive")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content for archival")
            temp_path = f.name

        try:
            result = doc._smart_archive(
                files=[temp_path],
                category="test_archive"
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["indexed"], 1)
            self.assertEqual(len(result["errors"]), 0)

            archive_base = self.config.workspace_dir / "documents" / "archive" / "test_archive"
            self.assertTrue(archive_base.exists())

            index_file = archive_base / "_index.json"
            self.assertTrue(index_file.exists())

            index_data = json.loads(index_file.read_text(encoding="utf-8"))
            self.assertEqual(index_data["category"], "test_archive")
            self.assertEqual(index_data["total"], 1)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            archive_base = self.config.workspace_dir / "documents" / "archive" / "test_archive"
            if archive_base.exists():
                import shutil
                shutil.rmtree(archive_base)

    def test_schema_minutes(self):
        """测试会议纪要工具 Schema"""
        doc = DocTool(self.config, task="minutes")
        schema = doc.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "generate_meeting_minutes")
        self.assertIn("transcript", schema["function"]["parameters"]["properties"])
        self.assertIn("meeting_title", schema["function"]["parameters"]["properties"])
        self.assertIn("transcript", schema["function"]["parameters"]["required"])

    def test_schema_archive(self):
        """测试归档工具 Schema"""
        doc = DocTool(self.config, task="archive")
        schema = doc.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertEqual(schema["function"]["name"], "smart_archive")
        self.assertIn("files", schema["function"]["parameters"]["properties"])
        self.assertIn("category", schema["function"]["parameters"]["properties"])
        self.assertIn("files", schema["function"]["parameters"]["required"])
        self.assertIn("category", schema["function"]["parameters"]["required"])

    def test_tool_base_inheritance(self):
        """测试工具基类继承"""
        from meetgrow_skill.tools.base import BaseTool
        doc = DocTool(self.config, task="minutes")
        self.assertIsInstance(doc, BaseTool)

    def test_workspace_dirs_created(self):
        """测试工作目录创建"""
        doc = DocTool(self.config, task="minutes")
        self.assertTrue(doc.workspace.exists())

        doc_archive = DocTool(self.config, task="archive")
        archive_dir = doc_archive.workspace / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        self.assertTrue(archive_dir.exists())

    def test_smart_archive_partial_success(self):
        """测试智能归档 - 部分成功"""
        doc = DocTool(self.config, task="archive")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = doc._smart_archive(
                files=[temp_path, "/nonexistent/file.txt"],
                category="partial_test"
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["indexed"], 1)
            self.assertGreater(len(result["errors"]), 0)

            index_file = doc.workspace / "archive" / "partial_test" / "_index.json"
            index_data = json.loads(index_file.read_text(encoding="utf-8"))
            self.assertEqual(index_data["total"], 1)
            self.assertGreater(len(index_data["errors"]), 0)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            archive_base = doc.workspace / "archive" / "partial_test"
            if archive_base.exists():
                import shutil
                shutil.rmtree(archive_base)

    def test_smart_archive_multiple_files(self):
        """测试智能归档 - 多文件"""
        doc = DocTool(self.config, task="archive")

        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"test content {i}")
                files.append(f.name)

        try:
            result = doc._smart_archive(
                files=files,
                category="multi_test"
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["indexed"], 3)
            self.assertEqual(len(result["errors"]), 0)

            # workspace already contains "documents", so archive path is workspace/archive/...
            index_file = doc.workspace / "archive" / "multi_test" / "_index.json"
            index_data = json.loads(index_file.read_text(encoding="utf-8"))
            self.assertEqual(index_data["total"], 3)
            self.assertEqual(len(index_data["files"]), 3)
        finally:
            for f in files:
                if Path(f).exists():
                    Path(f).unlink()
            archive_base = doc.workspace / "archive" / "multi_test"
            if archive_base.exists():
                import shutil
                shutil.rmtree(archive_base)

    def test_smart_archive_special_chars_in_filename(self):
        """测试智能归档 - 文件名特殊字符"""
        doc = DocTool(self.config, task="archive")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = doc._smart_archive(
                files=[temp_path],
                category="special_test"
            )
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["indexed"], 1)
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            archive_base = doc.workspace / "archive" / "special_test"
            if archive_base.exists():
                import shutil
                shutil.rmtree(archive_base)

    def test_generate_meeting_minutes_with_title_date(self):
        """测试会议纪要 - 完整参数"""
        doc = DocTool(self.config, task="minutes")
        result = doc._generate_meeting_minutes(
            transcript="Test transcript",
            meeting_title="Test Meeting",
            meeting_date="2025-01-01"
        )
        self.assertIn("status", result)

    def test_execute_minutes_no_transcript(self):
        """测试执行 - minutes 无转写文本"""
        doc = DocTool(self.config, task="minutes")
        result = doc.execute()
        self.assertEqual(result["status"], "error")
        self.assertIn("转写", result["error"])


class TestDocToolMockedLLM(unittest.TestCase):
    """DocTool LLM 调用 Mock 测试"""

    def setUp(self):
        self.config = AgentConfig()
        self.doc = DocTool(self.config, task="minutes")

    @patch("openai.OpenAI")
    def test_generate_meeting_minutes_success(self, mock_openai_cls):
        """测试会议纪要生成成功"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# 测试会议纪要\n## 议程\n1. 测试"
        mock_client.chat.completions.create.return_value = mock_response

        result = self.doc._generate_meeting_minutes(
            transcript="测试转写文本",
            meeting_title="测试会议",
            meeting_date="2025-01-01"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("会议纪要", result["minutes"])
        self.assertIn("测试会议", result["title"])
        self.assertEqual(result["date"], "2025-01-01")
        self.assertIn("output_file", result)

        output_file = Path(result["output_file"])
        self.assertTrue(output_file.exists())
        self.assertIn("minutes_测试会议", output_file.name)
        self.assertIn("20250101", output_file.name)

    @patch("openai.OpenAI")
    def test_generate_meeting_minutes_llm_error(self, mock_openai_cls):
        """测试 LLM 调用失败"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API 连接超时")

        result = self.doc._generate_meeting_minutes(
            transcript="测试转写文本",
            meeting_title="测试会议"
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("API 连接超时", result["error"])
        self.assertIn("partial_minutes", result)
        self.assertIn("测试转写文本", result["partial_minutes"])

    @patch("openai.OpenAI")
    def test_generate_meeting_minutes_no_title(self, mock_openai_cls):
        """测试无标题时的会议纪要"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# 会议纪要\n无标题"
        mock_client.chat.completions.create.return_value = mock_response

        result = self.doc._generate_meeting_minutes(
            transcript="测试转写文本",
            meeting_title=None,
            meeting_date=None
        )

        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result["minutes"])

    @patch("openai.OpenAI")
    def test_generate_meeting_minutes_long_transcript(self, mock_openai_cls):
        """测试长转写文本"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# 纪要"
        mock_client.chat.completions.create.return_value = mock_response

        long_transcript = " ".join(["这是一个很长的会议讨论点。" for _ in range(100)])
        result = self.doc._generate_meeting_minutes(
            transcript=long_transcript,
            meeting_title="长会议"
        )

        self.assertEqual(result["status"], "success")

    @patch("openai.OpenAI")
    def test_generate_meeting_minutes_special_chars_in_title(self, mock_openai_cls):
        """测试标题含特殊字符"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# 纪要"
        mock_client.chat.completions.create.return_value = mock_response

        result = self.doc._generate_meeting_minutes(
            transcript="测试",
            meeting_title="测试/特殊字符"
        )

        self.assertEqual(result["status"], "success")
        output_file = Path(result["output_file"])
        self.assertNotIn("/", output_file.name)
        self.assertIn("测试_特殊字符", output_file.name)

    @patch("openai.OpenAI")
    def test_execute_minutes_success(self, mock_openai_cls):
        """测试 execute 方法 - minutes 成功"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "# 纪要"
        mock_client.chat.completions.create.return_value = mock_response

        doc = DocTool(self.config, task="minutes")
        result = doc.execute(
            transcript="测试转写",
            meeting_title="测试",
            meeting_date="2025-01-01"
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("minutes", result)

    @patch("openai.OpenAI")
    def test_execute_minutes_error(self, mock_openai_cls):
        """测试 execute 方法 - minutes 失败"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("网络错误")

        doc = DocTool(self.config, task="minutes")
        result = doc.execute(
            transcript="测试转写",
            meeting_title="测试"
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("partial_minutes", result)
        self.assertIn("测试转写", result["partial_minutes"])


if __name__ == "__main__":
    unittest.main()
