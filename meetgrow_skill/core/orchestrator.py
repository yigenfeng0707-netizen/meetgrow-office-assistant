"""
MeetGrow AI Agent - 工具编排器
负责多工具的链式调度和结果传递
"""

import json
import logging
import time
from pathlib import Path
from typing import Any

from ..config import AgentConfig
from ..tools.ocr_tool import OCRTool
from ..tools.asr_tool import ASRTool
from ..tools.tts_tool import TTSTool
from ..tools.doc_tool import DocTool

logger = logging.getLogger(__name__)


class ToolOrchestrator:
    """工具编排器

    管理所有本地工具实例，负责任务分发和执行。
    """

    def __init__(self, config: AgentConfig):
        self.config = config

        # 注册所有工具
        self._tools = {
            "ocr_business_card": OCRTool(config, task="business_card"),
            "ocr_document": OCRTool(config, task="general"),
            "speech_to_text": ASRTool(config),
            "text_to_speech": TTSTool(config),
            "generate_meeting_minutes": DocTool(config, task="minutes"),
            "smart_archive": DocTool(config, task="archive"),
        }

        # 执行统计
        self._execution_log: list[dict] = []

    def execute(self, tool_name: str, args: dict) -> dict:
        """执行指定工具

        Args:
            tool_name: 工具名称
            args: 工具参数

        Returns:
            工具执行结果
        """
        start_time = time.time()

        try:
            tool = self._tools.get(tool_name)
            if tool is None:
                error_msg = f"未知工具: {tool_name}。可用工具: {list(self._tools.keys())}"
                logger.error(error_msg)
                return {"status": "error", "error": error_msg}

            logger.info(f"🚀 开始执行: {tool_name}")
            result = tool.execute(**args)

            elapsed = time.time() - start_time
            logger.info(f"✅ 完成: {tool_name} ({elapsed:.1f}s)")

            # 记录执行日志
            self._execution_log.append({
                "tool": tool_name,
                "args": args,
                "result_status": result.get("status", "unknown"),
                "elapsed_ms": round(elapsed * 1000),
                "timestamp": time.time()
            })

            return result

        except Exception as e:
            elapsed = time.time() - start_time
            error_result = {
                "status": "error",
                "error": str(e),
                "elapsed_ms": round(elapsed * 1000)
            }
            logger.error(f"❌ 执行失败: {tool_name} - {e}")
            return error_result

    def execute_chain(self, chain: list[tuple[str, dict]]) -> list[dict]:
        """链式执行多个工具

        前一个工具的输出可以作为后一个工具的输入。

        Args:
            chain: [(工具名, 参数), ...] 列表

        Returns:
            各工具执行结果列表
        """
        results = []
        context = {}  # 上下文传递

        for i, (tool_name, args) in enumerate(chain):
            # 注入前序结果
            merged_args = {**context, **args}
            result = self.execute(tool_name, merged_args)
            results.append(result)

            # 将结果注入到上下文中供后续工具使用
            if result.get("status") == "success":
                for key, value in result.items():
                    if key != "status":
                        context[key] = value

            # 如果失败，终止链
            if result.get("status") != "success":
                logger.warning(f"⛔ 链式执行终止于第 {i+1} 个工具: {tool_name}")
                break

        return results

    def get_status(self) -> dict:
        """获取工具状态和统计信息"""
        return {
            "registered_tools": list(self._tools.keys()),
            "execution_count": len(self._execution_log),
            "recent_logs": self._execution_log[-10:],  # 最近10条
        }
