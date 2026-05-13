"""
MeetGrow AI Agent - 记忆模块测试
"""

import sys
import tempfile
import json
from pathlib import Path
import unittest
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.core.memory import ConversationMemory


class TestConversationMemory(unittest.TestCase):
    """ConversationMemory 单元测试"""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.memory = ConversationMemory(Path(self.tmpdir))

    def tearDown(self):
        if Path(self.tmpdir).exists():
            shutil.rmtree(self.tmpdir)

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.memory)
        self.assertIsNotNone(self.memory._history)
        self.assertEqual(len(self.memory._history), 0)
        self.assertIsNotNone(self.memory._session_id)
        self.assertTrue(self.memory._session_id.startswith("session_"))

    def test_add_message(self):
        """测试添加消息"""
        self.memory.add_message("user", "你好")
        self.assertEqual(len(self.memory._history), 1)
        self.assertEqual(self.memory._history[0]["role"], "user")
        self.assertEqual(self.memory._history[0]["content"], "你好")
        self.assertIn("timestamp", self.memory._history[0])
        self.assertIn("metadata", self.memory._history[0])

    def test_add_multiple_messages(self):
        """测试添加多条消息"""
        self.memory.add_message("user", "你好")
        self.memory.add_message("assistant", "你好！有什么可以帮你？")
        self.memory.add_message("user", "识别这张名片")

        self.assertEqual(len(self.memory._history), 3)
        self.assertEqual(self.memory._history[0]["role"], "user")
        self.assertEqual(self.memory._history[1]["role"], "assistant")
        self.assertEqual(self.memory._history[2]["role"], "user")

    def test_add_messages_limit(self):
        """测试消息数量限制"""
        for i in range(55):
            self.memory.add_message("user", f"消息{i}")

        # 应限制在 50 条
        self.assertLessEqual(len(self.memory._history), 50)
        # 最后一条应该是 "消息54"
        self.assertEqual(self.memory._history[-1]["content"], "消息54")

    def test_get_context_messages(self):
        """测试获取上下文消息"""
        for i in range(5):
            self.memory.add_message("user", f"消息{i}")

        messages = self.memory.get_context_messages(3)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0]["content"], "消息2")
        self.assertEqual(messages[2]["content"], "消息4")

    def test_get_context_messages_fewer(self):
        """测试消息不足时返回全部"""
        self.memory.add_message("user", "消息1")
        self.memory.add_message("user", "消息2")

        messages = self.memory.get_context_messages(10)
        self.assertEqual(len(messages), 2)

    def test_clear_session(self):
        """测试清除会话"""
        self.memory.add_message("user", "消息1")
        self.memory.add_message("user", "消息2")
        self.memory.clear_session()
        self.assertEqual(len(self.memory._history), 0)
        # 会话 ID 应更新
        self.assertNotEqual(self.memory._session_id,
                           self.memory._generate_session_id()[:15])

    def test_add_tool_result(self):
        """测试添加工具结果"""
        self.memory.add_tool_result("ocr", {"status": "success", "name": "张三"})

        self.assertEqual(len(self.memory._history), 1)
        msg = self.memory._history[0]
        self.assertEqual(msg["role"], "tool")
        self.assertEqual(msg["metadata"]["tool"], "ocr")

    def test_update_user_context(self):
        """测试更新用户上下文"""
        self.memory.update_user_context("recent_contacts", ["张三", "李四"])
        self.assertEqual(self.memory._user_context["recent_contacts"],
                         ["张三", "李四"])

        # 验证文件已保存
        context_file = Path(self.tmpdir) / "user_context.json"
        self.assertTrue(context_file.exists())

    def test_get_user_context(self):
        """测试获取用户上下文"""
        self.memory.update_user_context("test_key", "test_value")

        # 获取特定 key
        self.assertEqual(self.memory.get_user_context("test_key"), "test_value")

        # 获取全部
        ctx = self.memory.get_user_context()
        self.assertIn("test_key", ctx)
        self.assertEqual(ctx["test_key"], "test_value")

    def test_get_user_context_missing_key(self):
        """测试获取不存在的 key"""
        result = self.memory.get_user_context("nonexistent_key")
        self.assertIsNone(result)

    def test_get_history_summary(self):
        """测试获取历史摘要"""
        self.memory.add_message("user", "你好")
        self.memory.add_tool_result("ocr", {"name": "张三"})
        self.memory.add_message("user", "转写语音")
        self.memory.add_tool_result("asr", {"text": "会议开始"})

        summary = self.memory.get_history_summary()
        self.assertEqual(summary["session_id"], self.memory._session_id)
        self.assertEqual(summary["message_count"], 4)
        self.assertEqual(len(summary["recent_tools"]), 2)
        self.assertIn("ocr", summary["recent_tools"])
        self.assertIn("asr", summary["recent_tools"])

    def test_persist_and_reload(self):
        """测试持久化保存和重新加载"""
        self.memory.add_message("user", "你好")
        self.memory.add_message("assistant", "你好！")
        self.memory._persist_history()

        # 重新加载
        history_file = Path(self.tmpdir) / "conversation_history.json"
        self.assertTrue(history_file.exists())

        loaded = json.loads(history_file.read_text(encoding="utf-8"))
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["content"], "你好")

    def test_message_metadata(self):
        """测试消息元数据"""
        self.memory.add_message("user", "测试", metadata={"priority": "high"})
        msg = self.memory._history[0]
        self.assertEqual(msg["metadata"]["priority"], "high")

    def test_default_metadata_empty(self):
        """测试默认空元数据"""
        self.memory.add_message("user", "测试")
        msg = self.memory._history[0]
        self.assertEqual(msg["metadata"], {})


if __name__ == "__main__":
    unittest.main()
