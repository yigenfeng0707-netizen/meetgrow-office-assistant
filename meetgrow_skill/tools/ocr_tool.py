"""
MeetGrow AI Agent - OCR 工具模块
基于 PaddleOCR 实现名片识别和文档识别
"""

import json
import logging
from pathlib import Path
from typing import Optional

from ..config import AgentConfig
from .base import BaseTool

logger = logging.getLogger(__name__)


class OCRTool(BaseTool):
    """OCR 工具 - 名片识别 / 文档识别

    使用 PaddleOCR (PP-OCRv5) 进行高精度中文 OCR。
    支持名片识别、通用文档识别、表格识别、票据识别。
    """

    def __init__(self, config: AgentConfig, task: str = "general"):
        super().__init__(config)
        self.task = task  # business_card, general, table, receipt
        self._ocr = None

    def _init_ocr(self):
        """初始化 PaddleOCR（懒加载）"""
        if self._ocr is not None:
            return

        try:
            from paddleocr import PaddleOCR

            logger.info("🔤 初始化 PaddleOCR...")
            self._ocr = PaddleOCR(
                lang=self.config.ocr_language,
            )
            logger.info("✅ PaddleOCR 初始化完成")
        except ImportError:
            logger.warning(
                "PaddleOCR 未安装，运行 'pip install paddlepaddle paddleocr'"
            )
            self._ocr = None

    def execute(self, image_path: str, **kwargs) -> dict:
        """执行 OCR 识别

        Args:
            image_path: 图片文件路径
            **kwargs: 额外参数

        Returns:
            OCR 识别结果
        """
        self._init_ocr()

        if self._ocr is None:
            return {
                "status": "error",
                "error": "PaddleOCR 未安装。请运行: pip install paddlepaddle paddleocr"
            }

        # 验证图片文件
        path = Path(image_path)
        if not path.exists():
            return {"status": "error", "error": f"文件不存在: {image_path}"}

        logger.info(f"🔍 OCR 识别: {image_path} (任务: {self.task})")

        try:
            # 执行 OCR
            result = self._ocr.ocr(str(path), cls=True)

            if not result or not result[0]:
                return {
                    "status": "success",
                    "text": "",
                    "message": "图片中未识别到文字"
                }

            # 解析识别结果
            texts = []
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                texts.append({
                    "text": text,
                    "confidence": round(confidence, 4),
                })

            full_text = "\n".join([t["text"] for t in texts])

            # 根据任务类型进行后处理
            processed = self._process_result(texts, full_text)

            return {
                "status": "success",
                "text": full_text,
                "lines": texts,
                "processed": processed,
                "task": self.task,
                "image": image_path,
            }

        except Exception as e:
            logger.error(f"OCR 执行失败: {e}")
            return {"status": "error", "error": str(e)}

    def _process_result(self, lines: list, full_text: str) -> dict:
        """根据任务类型后处理 OCR 结果

        Args:
            lines: 识别出的行列表
            full_text: 完整识别文本

        Returns:
            处理后的结构化结果
        """
        if self.task == "business_card":
            return self._parse_business_card(full_text)
        return {"raw_text": full_text}

    def _parse_business_card(self, text: str) -> dict:
        """尝试从 OCR 文本中解析名片信息

        名片识别是启发式的，基于常见格式：
        - 姓名: 通常有"姓名"/"Name"/"Mr."等标记
        - 公司: 通常包含"公司"/"Corp"/"Co."等
        - 电话: 匹配常见手机号/座机格式
        - 邮箱: 匹配邮箱格式
        - 职位: 通常包含"经理"/"总监"/"CEO"等

        Args:
            text: OCR 识别的完整文本

        Returns:
            结构化名片信息
        """
        import re

        info = {
            "name": "",
            "company": "",
            "title": "",
            "phone": "",
            "email": "",
            "address": "",
            "website": "",
            "raw_text": text
        }

        # 姓名: 优先匹配"姓名:"前缀，其次取第一行非空中文/英文(2-20字符)
        name_patterns = [
            r"(?:姓名|Name|名字)\s*:?\s*([^\n,：]{2,20})",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["name"] = match.group(1).strip()
                break
        if not info["name"]:
            first_line = text.split("\n")[0].strip()
            # 公司关键词过滤：避免把公司名称误识别为姓名
            company_keywords = ["公司", "企业", "集团", "corp", "inc", "ltd", "co.", "limited"]
            is_company_name = any(kw in first_line.lower() for kw in company_keywords)
            # 支持中文姓名 + 英文/国际姓名（2-20字符，字母/空格/连字符/句号）
            if 2 <= len(first_line) <= 20 and not is_company_name:
                is_chinese = any('\u4e00' <= c <= '\u9fff' for c in first_line)
                is_english = bool(re.match(r'^[a-zA-Z\s.\-\'"]+$', first_line))
                if is_chinese or is_english:
                    info["name"] = first_line

        # 电话
        phone_patterns = [
            r"((?:1[3-9][\d-]{9,12})|(?:\d{3,4}-?\d{7,8}))",
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                info["phone"] = match.group(1).strip()
                break

        # 邮箱
        email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        if email_match:
            info["email"] = email_match.group(1).strip()

        # 职位
        title_patterns = [
            r"((?:总|经|理|监|董|秘|主|高|C[EO][OFR])?(?:监|理|事|员|长|部|总|经|监)?(?:理|监)?(?:理)?(?:理)?)",
        ]
        # 更简单的方法: 找包含职位关键词的行
        for line in text.split("\n"):
            if any(kw in line for kw in ["经理", "总监", "CEO", "CFO", "COO",
                                          "总裁", "董事", "总经理", "副总",
                                          "Manager", "Director", "CEO", "President"]):
                info["title"] = line.strip()
                break

        # 公司和地址（其余文本）
        non_key_fields = []
        for line in text.split("\n"):
            line = line.strip()
            if line and not any(field in info for field in ["name", "phone", "email"] if info.get(field)):
                if info["title"] and info["title"] in line:
                    continue
                non_key_fields.append(line)

        if non_key_fields:
            info["company"] = non_key_fields[0] if len(non_key_fields) > 0 else ""
            if len(non_key_fields) > 1:
                info["address"] = " ".join(non_key_fields[1:])

        return info

    def get_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": f"ocr_{self.task}",
                "description": f"{'名片' if self.task == 'business_card' else '文档'} OCR 识别",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "image_path": {
                            "type": "string",
                            "description": "图片文件路径"
                        }
                    },
                    "required": ["image_path"]
                }
            }
        }
