"""
MeetGrow AI Agent - 文档处理工具模块
会议纪要生成、智能归档等文档处理能力
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from ..config import AgentConfig
from .base import BaseTool

logger = logging.getLogger(__name__)


class DocTool(BaseTool):
    """文档处理工具

    提供会议纪要生成、智能归档等文档处理能力。
    基于 Agent API 进行智能处理。
    """

    def __init__(self, config: AgentConfig, task: str = "minutes"):
        super().__init__(config)
        self.task = task  # minutes, archive
        self.workspace = config.workspace_dir / "documents"
        self.workspace.mkdir(parents=True, exist_ok=True)

    def execute(self, **kwargs) -> dict:
        """执行文档处理任务"""
        if self.task == "minutes":
            return self._generate_meeting_minutes(**kwargs)
        elif self.task == "archive":
            return self._smart_archive(**kwargs)
        else:
            return {"status": "error", "error": f"未知任务: {self.task}"}

    def _generate_meeting_minutes(self, transcript: str = None,
                                   meeting_title: str = None,
                                   meeting_date: str = None,
                                   **kwargs) -> dict:
        """生成会议纪要

        使用 Agent API 对转写文本进行智能整理，生成结构化纪要。

        Args:
            transcript: 会议转写文本
            meeting_title: 会议标题
            meeting_date: 会议日期

        Returns:
            结构化会议纪要
        """
        if not transcript:
            return {"status": "error", "error": "未提供转写文本"}

        # 构建提示词
        prompt = f"""请根据以下会议转写文本，生成一份结构化的会议纪要。

会议标题: {meeting_title or "未命名会议"}
会议日期: {meeting_date or datetime.now().strftime("%Y-%m-%d")}

--- 转写文本 ---
{transcript}
--- 结束 ---

请按以下格式输出会议纪要：

## {meeting_title or "会议纪要"}
- 日期: {meeting_date or datetime.now().strftime("%Y-%m-%d")}

### 议程
1. ...

### 会议摘要
（简要概括会议核心内容，200字以内）

### 讨论要点
1. ...

### 决策事项
- [ ] ...

### 待办事项
| 负责人 | 任务 | 截止日期 |
|--------|------|----------|
| ... | ... | ... |

### 下次会议计划
（如有）
"""
        # 调用 Agent API 生成
        from openai import OpenAI
        client = OpenAI(
            base_url=self.config.api_base_url,
            api_key=self.config.api_key or "placeholder"
        )

        try:
            response = client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": "你是专业的会议秘书，擅长从会议录音转写文本中提取关键信息，生成清晰的结构化会议纪要。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4096,
            )

            minutes_text = response.choices[0].message.content

            # 保存到文件
            safe_title = (meeting_title or "meeting").replace("/", "_")
            date_str = (meeting_date or datetime.now().strftime('%Y-%m-%d')).replace("-", "")
            output_file = self.workspace / f"minutes_{safe_title}_{date_str}.md"
            output_file.write_text(minutes_text, encoding="utf-8")

            return {
                "status": "success",
                "minutes": minutes_text,
                "output_file": str(output_file),
                "title": meeting_title,
                "date": meeting_date or datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            logger.error(f"会议纪要生成失败: {e}")
            return {
                "status": "error",
                "error": str(e),
                "partial_minutes": transcript[:500] + "..."  # 返回部分原始文本
            }

    def _smart_archive(self, files: list = None,
                       category: str = None,
                       **kwargs) -> dict:
        """智能归档

        Args:
            files: 文件路径列表
            category: 归档分类

        Returns:
            归档结果
        """
        if not files or not category:
            return {"status": "error", "error": "需要提供文件和分类信息"}

        archive_base = self.workspace / "archive" / category
        archive_base.mkdir(parents=True, exist_ok=True)

        indexed = 0
        errors = []

        for file_path in files:
            src = Path(file_path)
            if not src.exists():
                errors.append(f"文件不存在: {file_path}")
                continue

            # 生成规范文件名
            name_with_date = f"{datetime.now().strftime('%Y%m%d')}_{src.name}"
            dest = archive_base / name_with_date
            dest.parent.mkdir(parents=True, exist_ok=True)

            try:
                dest.write_bytes(src.read_bytes())
                indexed += 1
            except Exception as e:
                errors.append(f"{src.name}: {e}")

        # 生成索引文件
        index_file = archive_base / "_index.json"
        index_data = {
            "category": category,
            "date": datetime.now().isoformat(),
            "total": indexed,
            "errors": errors,
            "files": [
                {
                    "original": f,
                    "archived": str(archive_base / f"{datetime.now().strftime('%Y%m%d')}_{Path(f).name}"),
                }
                for f in files if f not in [e.split(":")[0] for e in errors]
            ]
        }
        index_file.write_text(json.dumps(index_data, ensure_ascii=False, indent=2))

        return {
            "status": "success",
            "archive_dir": str(archive_base),
            "indexed": indexed,
            "errors": errors,
            "index_file": str(index_file),
        }

    def get_schema(self) -> dict:
        if self.task == "minutes":
            return {
                "type": "function",
                "function": {
                    "name": "generate_meeting_minutes",
                    "description": "基于转写文本生成会议纪要",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "transcript": {"type": "string", "description": "会议转写文本"},
                            "meeting_title": {"type": "string", "description": "会议标题"},
                            "meeting_date": {"type": "string", "description": "会议日期 (YYYY-MM-DD)"},
                        },
                        "required": ["transcript", "meeting_title"]
                    }
                }
            }
        return {
            "type": "function",
            "function": {
                "name": "smart_archive",
                "description": "智能归档文件",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "files": {"type": "array", "items": {"type": "string"}},
                        "category": {"type": "string"},
                    },
                    "required": ["files", "category"]
                }
            }
        }
