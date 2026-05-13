"""
MeetGrow AI Agent - 核心 Agent 大脑模块
负责意图识别、工具选择、结果整合
"""

import json
import logging
from typing import Optional
from openai import OpenAI

from ..config import get_config
from ..skill import SkillDefinition, SkillMetadata
from .orchestrator import ToolOrchestrator

logger = logging.getLogger(__name__)


class MeetGrowAgent:
    """MeetGrow AI Agent 核心类
    
    作为 Agent 大脑，负责：
    1. 用户意图识别
    2. 工具选择和编排
    3. 结果整合与生成
    """

    # Agent 系统提示词模板
    SYSTEM_PROMPT = """你是一个会展招商办公提效智能助手（MeetGrow AI），运行在 Intel AI PC 上。

## 你的能力

你可以调用以下本地工具来完成办公提效任务：

{tool_descriptions}

## 工作流程

1. **理解意图**：分析用户请求，确定需要什么工具
2. **选择工具**：从可用工具中选择最合适的一个或多个
3. **编排执行**：按合理顺序调用工具
4. **整合结果**：汇总工具输出，生成用户友好的结果

## 约束

- 所有工具都在本地运行，尊重隐私
- 工具调用必须使用正确的参数格式
- 如果用户请求超出能力范围，明确说明
- 回答使用中文
"""

    def __init__(self, config=None):
        """初始化 Agent

        Args:
            config: AgentConfig 实例，默认使用全局配置
        """
        self.config = config or get_config()
        self.skill = SkillDefinition()
        self.orchestrator = ToolOrchestrator(self.config)
        self._client = None

        # 构建系统提示词
        self.system_prompt = self.SYSTEM_PROMPT.format(
            tool_descriptions="\n".join(self.skill.get_tool_descriptions())
        )

    def _get_client(self) -> OpenAI:
        """获取 OpenAI 兼容的 API 客户端"""
        if self._client is None:
            self._client = OpenAI(
                base_url=self.config.api_base_url,
                api_key=self.config.api_key or "placeholder"
            )
        return self._client

    def _call_llm(self, messages: list[dict], tools: list[dict]) -> dict:
        """调用 LLM API

        Args:
            messages: 对话消息列表
            tools: 工具定义列表

        Returns:
            API 响应
        """
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.config.model_name,
            messages=messages,
            tools=tools,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response

    def _get_tool_defs(self) -> list[dict]:
        """获取当前可用的工具定义"""
        return [tool.to_openai_format() for tool in self.skill.tools]

    def process(self, user_input: str, images: list[str] = None,
                audio_files: list[str] = None) -> str:
        """处理用户请求

        Args:
            user_input: 用户输入文本
            images: 可选的图片文件路径列表
            audio_files: 可选的音频文件路径列表

        Returns:
            Agent 的回复
        """
        # 构建初始消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        # 如果有附件信息，附加到消息中
        attachments = []
        if images:
            attachments.append(f"📎 附件 {len(images)} 个图片: {', '.join(images)}")
        if audio_files:
            attachments.append(f"🎙️ 附件 {len(audio_files)} 个音频: {', '.join(audio_files)}")
        if attachments:
            messages[-1]["content"] += "\n\n" + "\n".join(attachments)

        # 第一轮: LLM 决定使用哪些工具
        tools = self._get_tool_defs()
        response = self._call_llm(messages, tools)

        # 如果有工具调用
        if response.choices[0].message.tool_calls:
            final_messages = list(messages)  # 深拷贝
            final_messages.append(response.choices[0].message)

            results = []
            for tool_call in response.choices[0].message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                logger.info(f"🔧 调用工具: {tool_name}({tool_args})")

                # 执行工具
                tool_result = self.orchestrator.execute(tool_name, tool_args)
                results.append(tool_result)

                # 将工具结果追加到对话
                final_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False, default=str)
                })

            # 第二轮: LLM 根据工具结果生成最终回复
            second_response = self._call_llm(
                final_messages,
                tools=[]  # 不需要工具定义
            )

            return second_response.choices[0].message.content

        # 没有工具调用，直接返回 LLM 回复
        return response.choices[0].message.content

    def process_card_ocr(self, image_path: str) -> dict:
        """快捷方法: 名片 OCR 识别

        Args:
            image_path: 名片图片路径

        Returns:
            结构化联系人信息
        """
        return self.process(
            user_input=f"请识别这张名片: {image_path}",
            images=[image_path]
        )

    def process_meeting(self, audio_path: str, title: str = None) -> dict:
        """快捷方法: 会议录音转纪要

        Args:
            audio_path: 会议录音文件路径
            title: 会议标题

        Returns:
            会议纪要
        """
        return self.process(
            user_input=f"请将这份会议录音转写成纪要: {audio_path}" +
                       (f"，会议标题: {title}" if title else ""),
            audio_files=[audio_path]
        )
