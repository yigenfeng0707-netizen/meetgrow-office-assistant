"""
MeetGrow AI Agent - Skill 定义模块
定义 Skill 元数据和工具描述
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: dict
    examples: list

    def to_openai_format(self) -> dict:
        """转换为 OpenAI function calling 格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str = "meetgrow-office-assistant"
    version: str = "1.0.0"
    title: str = "MeetGrow AI PC Agent Skill"
    description: str = (
        "会展招商办公提效工具。支持名片 OCR 识别、会议纪要生成、"
        "语音转写、语音播报等功能。基于 Intel AI PC 本地运行。"
    )
    author: str = "WinClaw"
    license: str = "MIT"
    tags: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = ["agent", "ocr", "asr", "tts", "office", "intel-ai-pc"]


@dataclass
class SkillDefinition:
    """完整 Skill 定义"""

    def __init__(self):
        self.metadata = SkillMetadata()

        # 定义所有可用工具
        self.tools = [
            ToolDefinition(
                name="ocr_business_card",
                description=(
                    "识别名片图片，提取姓名、公司、职位、电话、邮箱等信息。\n"
                    "输入: 图片文件路径\n"
                    "输出: 结构化联系人 JSON\n"
                    "支持: 中英文名片、横版/竖版/方形名片"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "名片图片的本地文件路径"
                        }
                    },
                    "required": ["image_path"]
                },
                examples=[
                    {
                        "input": {"image_path": "/path/to/card.jpg"},
                        "output": {
                            "status": "success",
                            "contacts": [
                                {
                                    "name": "张三",
                                    "company": "XX科技有限公司",
                                    "title": "采购总监",
                                    "phone": "138-0000-0000",
                                    "email": "zhangsan@example.com"
                                }
                            ]
                        }
                    }
                ]
            ),

            ToolDefinition(
                name="ocr_document",
                description=(
                    "识别文档/票据图片中的文字内容。\n"
                    "输入: 图片文件路径\n"
                    "输出: 识别出的文本\n"
                    "支持: 中文、英文、中英混合、表格、票据"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "文档图片的本地文件路径"
                        },
                        "task": {
                            "type": "string",
                            "enum": ["general", "table", "receipt"],
                            "description": "识别任务类型: general(通用文本)/table(表格)/receipt(票据)"
                        }
                    },
                    "required": ["image_path"]
                },
                examples=[
                    {
                        "input": {"image_path": "/path/to/doc.jpg", "task": "general"},
                        "output": {
                            "status": "success",
                            "text": "识别出的文档文本..."
                        }
                    }
                ]
            ),

            ToolDefinition(
                name="speech_to_text",
                description=(
                    "将语音/会议录音文件转换为文字。\n"
                    "输入: 音频文件路径 (wav/mp3/m4a)\n"
                    "输出: 带时间戳的转写文本\n"
                    "支持: 中文、中英混合、说话人分离"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "audio_path": {
                            "type": "string",
                            "description": "音频文件的本地路径"
                        },
                        "diarization": {
                            "type": "boolean",
                            "description": "是否启用说话人分离",
                            "default": False
                        }
                    },
                    "required": ["audio_path"]
                },
                examples=[
                    {
                        "input": {
                            "audio_path": "/path/to/meeting.wav",
                            "diarization": True
                        },
                        "output": {
                            "status": "success",
                            "transcript": [
                                {"speaker": "speaker_0", "start": 0.0, "end": 5.2, "text": "大家好，现在开始..."},
                                {"speaker": "speaker_1", "start": 5.5, "end": 10.1, "text": "我先汇报一下..."}
                            ]
                        }
                    }
                ]
            ),

            ToolDefinition(
                name="text_to_speech",
                description=(
                    "将文本转换为语音播报。\n"
                    "输入: 文本字符串\n"
                    "输出: 音频文件路径\n"
                    "支持: 中文女声(小晓)、男声(云扬)"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "需要转换的文本内容"
                        },
                        "voice": {
                            "type": "string",
                            "description": "声音选择: 小晓(默认女声)/云扬(男声)/晓晓(活泼女声)"
                        }
                    },
                    "required": ["text"]
                },
                examples=[
                    {
                        "input": {"text": "今天的会议有3项议程...", "voice": "小晓"},
                        "output": {
                            "status": "success",
                            "audio_path": "/path/to/output.mp3"
                        }
                    }
                ]
            ),

            ToolDefinition(
                name="generate_meeting_minutes",
                description=(
                    "基于转写文本生成会议纪要。\n"
                    "输入: 转写文本 + 会议基本信息\n"
                    "输出: 结构化会议纪要(议程、摘要、决策、待办)\n"
                    "由 Agent 内部调用, 自动整合 OCR + ASR + 摘要能力"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "transcript": {
                            "type": "string",
                            "description": "会议转写文本"
                        },
                        "meeting_title": {
                            "type": "string",
                            "description": "会议标题"
                        },
                        "meeting_date": {
                            "type": "string",
                            "description": "会议日期 (YYYY-MM-DD)"
                        }
                    },
                    "required": ["transcript", "meeting_title"]
                },
                examples=[
                    {
                        "input": {
                            "transcript": "会议完整转写文本...",
                            "meeting_title": "Q2 招商推进会",
                            "meeting_date": "2026-05-08"
                        },
                        "output": {
                            "status": "success",
                            "minutes": {
                                "title": "Q2 招商推进会纪要",
                                "date": "2026-05-08",
                                "agenda": ["...", "..."],
                                "summary": "...",
                                "decisions": ["..."],
                                "action_items": [
                                    {"assignee": "...", "task": "...", "deadline": "..."}
                                ]
                            }
                        }
                    }
                ]
            ),

            ToolDefinition(
                name="smart_archive",
                description=(
                    "智能归档工具。\n"
                    "输入: 文件路径列表 + 分类标签\n"
                    "输出: 归档目录结构和索引文件\n"
                    "支持: 自动分类、命名规范、索引生成"
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "待归档文件路径列表"
                        },
                        "category": {
                            "type": "string",
                            "description": "归档分类 (如: 2026-05-名片/2026-05/会议纪要)"
                        }
                    },
                    "required": ["files", "category"]
                },
                examples=[
                    {
                        "input": {
                            "files": ["/path/to/a.jpg", "/path/to/b.jpg"],
                            "category": "2026-05/名片"
                        },
                        "output": {
                            "status": "success",
                            "archive_dir": "/meetgrow_data/archive/2026-05/名片",
                            "indexed": 2
                        }
                    }
                ]
            )
        ]

    def get_tool_names(self) -> list[str]:
        """获取所有可用工具名称"""
        return [t.name for t in self.tools]

    def get_tool_descriptions(self) -> list[str]:
        """获取工具描述（用于提示词）"""
        return [f"{t.name}: {t.description}" for t in self.tools]
