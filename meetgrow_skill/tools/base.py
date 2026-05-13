"""
MeetGrow AI Agent - 工具基类
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from ..config import AgentConfig


class BaseTool(ABC):
    """所有工具的基类"""

    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def execute(self, **kwargs) -> dict:
        """执行工具操作

        Args:
            **kwargs: 工具参数

        Returns:
            {
                "status": "success" | "error",
                "data": <执行结果>,
                ...其他字段
            }
        """
        pass

    @abstractmethod
    def get_schema(self) -> dict:
        """获取工具参数 Schema"""
        pass

    def validate_path(self, path_str: str, required: bool = True) -> Path:
        """验证文件路径"""
        path = Path(path_str)
        if not path.exists():
            return {"status": "error", "error": f"文件不存在: {path_str}"}
        return path
