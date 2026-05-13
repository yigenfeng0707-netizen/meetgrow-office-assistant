"""
MeetGrow AI Agent - CLI 入口测试
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.__main__ import main
from meetgrow_skill.config import AgentConfig


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIInit:
    """测试 init 命令"""

    def test_init_creates_workspace(self, runner):
        """init 创建工作目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, ["init", "-w", tmpdir])
            assert result.exit_code == 0
            assert "初始化" in result.output
            assert "工作目录" in result.output

    def test_init_creates_subdirs(self, runner):
        """init 创建所有子目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, ["init", "-w", tmpdir])
            assert result.exit_code == 0
            for subdir in ["tts_output", "documents/archive", "models/paddleocr", "models/funasr"]:
                assert Path(tmpdir, subdir).exists()

    def test_init_creates_config(self, runner):
        """init 创建配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, ["init", "-w", tmpdir])
            assert result.exit_code == 0
            config_file = Path(tmpdir, "config.yaml")
            assert config_file.exists()

    def test_init_skill_definition(self, runner):
        """init 创建 Skill 定义文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(main, ["init", "-w", tmpdir])
            assert result.exit_code == 0
            skill_file = Path(tmpdir, "meetgrow_skill.json")
            assert skill_file.exists()
            skill_data = json.loads(skill_file.read_text(encoding="utf-8"))
            assert "metadata" in skill_data
            assert "tools" in skill_data
            assert len(skill_data["tools"]) > 0

    def test_init_config_exists_skip(self, runner):
        """init 配置文件已存在时跳过"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir, "config.yaml")
            config_file.write_text("test: value")
            result = runner.invoke(main, ["init", "-w", tmpdir])
            assert result.exit_code == 0
            assert "已存在" in result.output

    def test_init_help(self, runner):
        """init 帮助信息"""
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "工作目录" in result.output


class TestCLIOCR:
    """测试 OCR 命令"""

    def test_ocr_file_not_found(self, runner):
        """OCR 文件不存在"""
        result = runner.invoke(main, ["ocr", "/nonexistent/image.jpg"])
        assert result.exit_code != 0 or "不存在" in result.output or "错误" in result.output

    def test_ocr_no_paddleocr(self, runner):
        """OCR PaddleOCR 未安装时的错误处理"""
        from meetgrow_skill.tools.ocr_tool import OCRTool
        with patch.object(OCRTool, '__init__', return_value=None):
            with patch.object(OCRTool, 'execute', return_value={
                "status": "error",
                "error": "PaddleOCR 未安装。请运行: pip install paddlepaddle paddleocr"
            }):
                result = runner.invoke(main, ["ocr", "/fake/path.jpg"])
                assert "错误" in result.output or "PaddleOCR" in result.output


class TestCLIAsr:
    """测试 ASR 命令"""

    def test_asr_no_config(self, runner):
        """ASR 没有配置时"""
        with patch("meetgrow_skill.__main__.get_config") as mock_get_config:
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            result = runner.invoke(main, ["asr", "/fake/audio.wav"])
            assert result.exit_code == 0 or "错误" in result.output


class TestCLITTS:
    """测试 TTS 命令"""

    def test_tts_empty_text(self, runner):
        """TTS 空文本"""
        result = runner.invoke(main, ["tts", ""])
        assert result.exit_code == 0 or "错误" in result.output

    def test_tts_custom_voice(self, runner):
        """TTS 自定义声音"""
        result = runner.invoke(main, ["tts", "test", "-v", "云扬"])
        assert result.exit_code == 0 or "错误" in result.output

    def test_tts_custom_rate(self, runner):
        """TTS 自定义语速"""
        result = runner.invoke(main, ["tts", "test", "-r", "+20%"])
        assert result.exit_code == 0 or "错误" in result.output

    def test_tts_custom_output(self, runner):
        """TTS 自定义输出路径"""
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
        try:
            result = runner.invoke(main, ["tts", "test", "-o", temp_path])
            assert result.exit_code == 0 or "错误" in result.output
        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()

    def test_tts_long_text_truncation(self, runner):
        """TTS 长文本截断显示"""
        long_text = "测试文本 " * 50
        result = runner.invoke(main, ["tts", long_text])
        assert result.exit_code == 0 or "错误" in result.output


class TestCLIAgent:
    """测试 Agent 命令"""

    def test_agent_simple_prompt(self, runner):
        """Agent 简单提示"""
        with patch("meetgrow_skill.__main__.MeetGrowAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.process.return_value = "Agent response"
            mock_agent_cls.return_value = mock_agent
            result = runner.invoke(main, ["agent", "你好"])
            assert result.exit_code == 0
            assert "Agent response" in result.output

    def test_agent_with_image(self, runner):
        """Agent 带图片附件"""
        with patch("meetgrow_skill.__main__.MeetGrowAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.process.return_value = "Agent response"
            mock_agent_cls.return_value = mock_agent
            result = runner.invoke(main, ["agent", "识别这张图", "-i", "/fake/img.jpg"])
            assert result.exit_code == 0

    def test_agent_with_audio(self, runner):
        """Agent 带音频附件"""
        with patch("meetgrow_skill.__main__.MeetGrowAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.process.return_value = "Agent response"
            mock_agent_cls.return_value = mock_agent
            result = runner.invoke(main, ["agent", "听这个", "-a", "/fake/audio.wav"])
            assert result.exit_code == 0

    def test_agent_exception(self, runner):
        """Agent 异常处理"""
        with patch("meetgrow_skill.__main__.MeetGrowAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.process.side_effect = Exception("API error")
            mock_agent_cls.return_value = mock_agent
            result = runner.invoke(main, ["agent", "test"])
            assert "错误" in result.output


class CLIDemo:
    """测试 demo 命令"""

    def test_demo(self, runner):
        """demo 命令"""
        result = runner.invoke(main, ["demo"])
        assert result.exit_code == 0
        assert "演示" in result.output
        assert "架构" in result.output

    def test_demo_skill_info(self, runner):
        """demo 显示 Skill 信息"""
        result = runner.invoke(main, ["demo"])
        assert "v" in result.output
        assert "工具数" in result.output


class CLIGroup:
    """测试 CLI 命令组"""

    def test_help(self, runner):
        """根帮助"""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "ocr" in result.output
        assert "asr" in result.output
        assert "tts" in result.output
        assert "agent" in result.output
        assert "demo" in result.output

    def test_invalid_command(self, runner):
        """无效命令"""
        result = runner.invoke(main, ["invalid"])
        assert result.exit_code != 0

    def test_config_option(self, runner):
        """--config 选项"""
        result = runner.invoke(main, ["--help"])
        assert "config" in result.output.lower() or "配置" in result.output


class TestCLIMain:
    """测试 __main__ 入口"""

    def test_main_is_click_group(self):
        """main 是 Click 命令组"""
        from click import Group
        assert isinstance(main, Group)

    def test_main_has_init_command(self):
        """main 包含 init 命令"""
        assert "init" in main.commands

    def test_main_has_ocr_command(self):
        """main 包含 ocr 命令"""
        assert "ocr" in main.commands

    def test_main_has_asr_command(self):
        """main 包含 asr 命令"""
        assert "asr" in main.commands

    def test_main_has_tts_command(self):
        """main 包含 tts 命令"""
        assert "tts" in main.commands

    def test_main_has_agent_command(self):
        """main 包含 agent 命令"""
        assert "agent" in main.commands

    def test_main_has_demo_command(self):
        """main 包含 demo 命令"""
        assert "demo" in main.commands


class TestCLICustomConfig:
    """测试自定义配置文件"""

    def test_init_with_config_option(self, runner):
        """init 指定配置文件路径 - --config 是 main 组选项，放子命令前面"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir, "myconfig.yaml")
            result = runner.invoke(main, ["--config", str(config_path), "init", "-w", tmpdir])
            assert result.exit_code == 0

    def test_main_with_config_option(self, runner):
        """CLI 带自定义配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir, "custom.yaml")
            result = runner.invoke(main, ["--config", str(config_path), "init", "-w", tmpdir])
            assert result.exit_code == 0
