"""
MeetGrow AI Agent - OCR 工具测试
"""

import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch, Mock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import AgentConfig
from meetgrow_skill.tools.ocr_tool import OCRTool


class TestOCRTool(unittest.TestCase):
    """OCR 工具单元测试"""

    def setUp(self):
        self.config = AgentConfig()
        self.ocr = OCRTool(self.config, task="general")

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.ocr.config)
        self.assertEqual(self.ocr.task, "general")

    def test_business_card_task(self):
        """测试名片识别任务"""
        ocr_card = OCRTool(self.config, task="business_card")
        self.assertEqual(ocr_card.task, "business_card")

    def test_parse_business_card_basic(self):
        """测试名片解析基础逻辑"""
        ocr = OCRTool(self.config, task="business_card")

        test_text = """张三
XX科技有限公司
采购总监
电话: 138-0000-0000
邮箱: zhangsan@example.com
地址: 上海市浦东新区"""

        result = ocr._parse_business_card(test_text)
        self.assertEqual(result["name"], "张三")
        self.assertEqual(result["phone"], "138-0000-0000")
        self.assertIn("zhangsan@example.com", result["email"] or "")
        self.assertIn("采购总监", result["title"] or "")

    def test_parse_business_card_name_prefix(self):
        """测试名片解析 - 姓名带前缀"""
        ocr = OCRTool(self.config, task="business_card")
        test_text = "姓名: 李四\nABC公司\n经理"
        result = ocr._parse_business_card(test_text)
        self.assertEqual(result["name"], "李四")

    def test_parse_business_card_no_name(self):
        """测试名片解析 - 无姓名"""
        ocr = OCRTool(self.config, task="business_card")
        result = ocr._parse_business_card("只有公司信息\n地址: 北京")
        self.assertEqual(result["name"], "")

    def test_parse_business_card_no_phone(self):
        """测试名片解析 - 无电话"""
        ocr = OCRTool(self.config, task="business_card")
        result = ocr._parse_business_card("张三\n公司\n邮箱: test@test.com")
        self.assertEqual(result["phone"], "")

    def test_parse_business_card_empty(self):
        """测试名片解析 - 空文本"""
        ocr = OCRTool(self.config, task="business_card")
        result = ocr._parse_business_card("")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "")

    def test_parse_business_card_international(self):
        """测试名片解析 - 英文名片"""
        ocr = OCRTool(self.config, task="business_card")
        test_text = "John Smith\nABC Corp\nManager\njohn@example.com"
        result = ocr._parse_business_card(test_text)
        self.assertEqual(result["name"], "John Smith")
        self.assertIn("john@example.com", result["email"] or "")

    def test_parse_business_card_with_ceo(self):
        """测试名片解析 - CEO 职位"""
        ocr = OCRTool(self.config, task="business_card")
        test_text = "王五\nXX科技\nCEO\nwang@company.com"
        result = ocr._parse_business_card(test_text)
        self.assertIn("CEO", result["title"] or "")

    def test_parse_business_card_with_director(self):
        """测试名片解析 - Director 职位"""
        ocr = OCRTool(self.config, task="business_card")
        test_text = "赵六\nYY公司\nDirector\nzhao@yy.com"
        result = ocr._parse_business_card(test_text)
        self.assertIn("Director", result["title"] or "")

    def test_execute_without_paddleocr(self):
        """测试 PaddleOCR 未安装时的行为"""
        with patch.object(self.ocr, '_init_ocr'):
            self.ocr._ocr = None
            result = self.ocr.execute(image_path="/fake/image.jpg")
            self.assertEqual(result["status"], "error")
            self.assertIn("PaddleOCR 未安装", result["error"])

    def test_file_not_found(self):
        """测试文件不存在时的错误处理"""
        result = self.ocr.execute(image_path="/nonexistent/path/image.jpg")
        self.assertEqual(result["status"], "error")
        self.assertIn("不存在", result["error"])

    def test_execute_with_paddleocr_success(self):
        """测试 PaddleOCR 正常执行"""
        mock_result = [[
            ["/fake/rect", ["公司", 0.99], [0, 0, 100, 50]],
            ["/fake/rect", ["张三", 0.95], [0, 0, 100, 50]],
        ]]

        with patch.object(self.ocr, '_init_ocr'):
            self.ocr._ocr = MagicMock()
            self.ocr._ocr.ocr.return_value = mock_result

            # 创建一个临时图片文件
            from pathlib import Path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'\xff\xd8\xff\xe0')
                img_path = f.name

            try:
                result = self.ocr.execute(image_path=img_path)
                self.assertEqual(result["status"], "success")
                self.assertIn("公司", result["text"])
                self.assertIn("张三", result["text"])
                self.assertEqual(len(result["lines"]), 2)
            finally:
                Path(img_path).unlink()

    def test_execute_empty_result(self):
        """测试 PaddleOCR 返回空结果"""
        with patch.object(self.ocr, '_init_ocr'):
            self.ocr._ocr = MagicMock()
            self.ocr._ocr.ocr.return_value = None

            from pathlib import Path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'\xff\xd8\xff\xe0')
                img_path = f.name

            try:
                result = self.ocr.execute(image_path=img_path)
                self.assertEqual(result["status"], "success")
                self.assertEqual(result["text"], "")
                self.assertIn("未识别到文字", result.get("message", ""))
            finally:
                Path(img_path).unlink()

    def test_execute_exception(self):
        """测试 PaddleOCR 执行异常"""
        with patch.object(self.ocr, '_init_ocr'):
            self.ocr._ocr = MagicMock()
            self.ocr._ocr.ocr.side_effect = Exception("PaddleOCR 运行时错误")

            from pathlib import Path
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(b'\xff\xd8\xff\xe0')
                img_path = f.name

            try:
                result = self.ocr.execute(image_path=img_path)
                self.assertEqual(result["status"], "error")
                self.assertIn("PaddleOCR 运行时错误", result["error"])
            finally:
                Path(img_path).unlink()

    def test_process_result_general(self):
        """测试通用任务后处理"""
        self.ocr.task = "general"
        result = self.ocr._process_result(
            lines=[{"text": "hello", "confidence": 0.9}],
            full_text="hello"
        )
        self.assertIn("raw_text", result)
        self.assertEqual(result["raw_text"], "hello")

    def test_process_result_business_card(self):
        """测试名片任务后处理"""
        self.ocr.task = "business_card"
        result = self.ocr._process_result(
            lines=[{"text": "张三", "confidence": 0.95}],
            full_text="张三\nXX公司"
        )
        self.assertIn("name", result)
        self.assertEqual(result["name"], "张三")

    def test_get_schema_general(self):
        """测试通用任务 Schema"""
        self.ocr.task = "general"
        schema = self.ocr.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertIn("function", schema)
        self.assertIn("image_path", schema["function"]["parameters"]["properties"])
        self.assertIn("image_path", schema["function"]["parameters"]["required"])

    def test_get_schema_business_card(self):
        """测试名片任务 Schema"""
        self.ocr.task = "business_card"
        schema = self.ocr.get_schema()
        self.assertEqual(schema["type"], "function")
        self.assertIn("function", schema)
        self.assertIn("image_path", schema["function"]["parameters"]["properties"])
        self.assertIn("image_path", schema["function"]["parameters"]["required"])

    def test_schema_function_name(self):
        """测试 Schema 函数名"""
        ocr_general = OCRTool(self.config, task="general")
        ocr_card = OCRTool(self.config, task="business_card")
        self.assertIn("ocr_", ocr_general.get_schema()["function"]["name"])
        self.assertIn("ocr_", ocr_card.get_schema()["function"]["name"])


class TestOCRToolValidation(unittest.TestCase):
    """OCR 工具输入验证"""

    def setUp(self):
        self.config = AgentConfig()
        self.ocr = OCRTool(self.config, task="general")

    def test_empty_text(self):
        """测试空文本处理"""
        result = self.ocr._parse_business_card("")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "")

    def test_whitespace_text(self):
        """测试空白文本"""
        result = self.ocr._parse_business_card("   \n  \n  ")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "")

    def test_single_char_name(self):
        """测试单字符姓名（太短）"""
        result = self.ocr._parse_business_card("张\n公司\n电话: 13800000000")
        self.assertEqual(result["name"], "")  # 单字符太短

    def test_long_name_truncated(self):
        """测试超长姓名截断"""
        long_name = "赵" * 25  # 超过20字符
        result = self.ocr._parse_business_card(f"{long_name}\n公司")
        self.assertEqual(result["name"], "")  # 太长也拿不到

    def test_mobile_phone_patterns(self):
        """测试手机号匹配多种格式"""
        ocr = OCRTool(self.config, task="business_card")

        # 带横杠
        r1 = ocr._parse_business_card("张三\n电话: 138-0000-0000")
        self.assertEqual(r1["phone"], "138-0000-0000")

        # 纯数字
        r2 = ocr._parse_business_card("张三\n13800000001")
        self.assertIn("13800000001", r2["phone"])

    def test_landline_phone_patterns(self):
        """测试固话匹配"""
        ocr = OCRTool(self.config, task="business_card")
        r = ocr._parse_business_card("张三\n座机: 010-12345678")
        self.assertIn("010", r["phone"])

    def test_no_email(self):
        """测试无邮箱情况"""
        ocr = OCRTool(self.config, task="business_card")
        r = ocr._parse_business_card("张三\n公司")
        self.assertEqual(r["email"], "")


class TestOCRToolMock(unittest.TestCase):
    """OCR 工具 Mock 测试"""

    def setUp(self):
        self.config = AgentConfig()
        self.ocr = OCRTool(self.config, task="general")

    def test_init_ocr_already_initialized(self):
        """测试 OCR 已初始化时不重复初始化"""
        self.ocr._ocr = MagicMock()
        with patch('paddleocr.PaddleOCR') as mock_ocr:
            self.ocr._init_ocr()
            mock_ocr.assert_not_called()

    def test_init_ocr_import_error(self):
        """测试 PaddleOCR 导入失败"""
        with patch.dict('sys.modules', {'paddleocr': None}):
            self.ocr._init_ocr()
            self.assertIsNone(self.ocr._ocr)


if __name__ == "__main__":
    unittest.main()
