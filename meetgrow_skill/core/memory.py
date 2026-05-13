"""
MeetGrow AI Agent - 对话记忆 / 上下文管理
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ConversationMemory:
    """对话记忆模块

    管理 Agent 的上下文信息，包括：
    - 历史对话
    - 工具调用结果
    - 用户偏好
    - 会话状态
    """

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self._history: list[dict] = []
        self._user_context: dict = {}
        self._session_id: str = self._generate_session_id()

        # 确保目录存在
        self._history_file = workspace_dir / "conversation_history.json"
        self._context_file = workspace_dir / "user_context.json"

        self._load_context()

    def _generate_session_id(self) -> str:
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")

    def _load_context(self):
        """加载用户上下文"""
        if self._context_file.exists():
            try:
                self._user_context = json.loads(self._context_file.read_text())
                logger.debug(f"加载用户上下文: {list(self._user_context.keys())}")
            except Exception as e:
                logger.warning(f"加载上下文失败: {e}")

    def save_context(self):
        """保存用户上下文"""
        try:
            self._context_file.write_text(
                json.dumps(self._user_context, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            logger.warning(f"保存上下文失败: {e}")

    def add_message(self, role: str, content: str, metadata: dict = None):
        """添加对话消息"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self._history.append(message)

        # 限制历史长度（最多 50 条，保留最近上下文）
        if len(self._history) > 50:
            self._history = self._history[-50:]

        # 定期持久化
        if len(self._history) % 10 == 0:
            self._persist_history()

    def add_tool_result(self, tool_name: str, result: dict):
        """添加工具调用结果到历史"""
        self.add_message(
            role="tool",
            content=json.dumps(result, ensure_ascii=False, default=str),
            metadata={"tool": tool_name}
        )

    def get_context_messages(self, limit: int = 20) -> list[dict]:
        """获取上下文消息（用于发送给 LLM）

        Args:
            limit: 最大返回消息数

        Returns:
            最近 N 条消息（不包括 tool 角色，因为 tool 结果已单独处理）
        """
        # 获取最近的消息
        messages = self._history[-limit:]

        # 构建系统消息
        context_info = []
        if self._user_context.get("recent_contacts"):
            context_info.append(f"最近联系人数: {len(self._user_context['recent_contacts'])}")
        if self._user_context.get("last_meeting"):
            context_info.append(f"上次会议: {self._user_context['last_meeting']}")

        return messages

    def update_user_context(self, key: str, value):
        """更新用户上下文"""
        self._user_context[key] = value
        self.save_context()

    def get_user_context(self, key: str = None):
        """获取用户上下文"""
        if key is None:
            return self._user_context.copy()
        return self._user_context.get(key)

    def clear_session(self):
        """清除当前会话"""
        self._persist_history()
        self._history = []
        self._session_id = self._generate_session_id()
        logger.info("会话已清除")

    def _persist_history(self):
        """持久化历史到文件"""
        try:
            self._history_file.write_text(
                json.dumps(self._history, ensure_ascii=False, indent=2)
            )
        except Exception as e:
            logger.warning(f"持久化历史失败: {e}")

    def get_history_summary(self) -> dict:
        """获取会话摘要"""
        return {
            "session_id": self._session_id,
            "message_count": len(self._history),
            "recent_tools": [
                m.get("metadata", {}).get("tool")
                for m in self._history[-10:]
                if m.get("role") == "tool"
            ],
        }
