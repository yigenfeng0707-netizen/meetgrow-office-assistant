"""
MeetGrow AI Agent - Agent 核心测试
测试 MeetGrowAgent 的完整功能：初始化、LLM 调用、工具编排、快捷方法
所有外部依赖（LLM API）均已 Mock，无需网络请求
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockToolInstance:
    """轻量级 Mock 工具实例"""
    def __init__(self, config=None, task=None, **kwargs):
        self.config = config
        self.task = task
        self._schema_name = {
            "business_card": "ocr_business_card",
            "general": "ocr_general",
            "minutes": "generate_meeting_minutes",
            "archive": "smart_archive",
        }.get(task, f"tool_{task}")
        self._voice_aliases = {
            "xiaoxiao": "zh-CN-XiaoxiaoNeural",
            "xiaoyi": "zh-CN-XiaoyiNeural",
            "yunyang": "zh-CN-YunyangNeural",
        }

    def get_schema(self):
        return {
            "type": "function",
            "function": {
                "name": self._schema_name,
                "description": "Mock tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }

    def execute(self, **kwargs):
        return {"status": "success", "result": "Mock result"}


class TestAgentInitialization(unittest.TestCase):
    """测试 Agent 初始化"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_init_with_custom_config(self, mock_orchestrator_cls):
        """测试使用自定义配置初始化 Agent"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        # 验证所有初始化属性
        self.assertIsNotNone(agent.config)
        self.assertEqual(agent.config.model_name, "qwen3.6-35b-a3b")
        self.assertEqual(agent.config.api_base_url, "http://test-api:11434/v1")
        self.assertIsNotNone(agent.skill)
        self.assertEqual(agent.skill.metadata.name, "meetgrow-office-assistant")
        self.assertIsNotNone(agent.orchestrator)
        self.assertIsNone(agent._client)
        self.assertIn("工具", agent.system_prompt)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_init_without_config(self, mock_orchestrator_cls):
        """测试不传配置时使用默认配置"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        self.assertIsNotNone(agent.config)
        self.assertIsNotNone(agent.skill)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_tool_count(self, mock_orchestrator_cls):
        """测试工具数量正确"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)
        self.assertEqual(len(agent.skill.tools), 6)


class TestAgentClient(unittest.TestCase):
    """测试 Agent 客户端管理"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="my-api-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_client_lazy_initialization(self, mock_orchestrator_cls):
        """测试客户端懒加载"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)
        self.assertIsNone(agent._client)

        # 第一次调用应创建客户端
        with patch("meetgrow_skill.core.agent.OpenAI") as mock_openai_cls:
            mock_openai_cls.return_value = MagicMock()
            client = agent._get_client()
            self.assertIsNotNone(client)
            # 验证 OpenAI 被正确调用
            mock_openai_cls.assert_called_once()
            call_kwargs = mock_openai_cls.call_args
            self.assertEqual(call_kwargs[1]["base_url"], "http://test-api:11434/v1")
            self.assertEqual(call_kwargs[1]["api_key"], "my-api-key")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_client_caching(self, mock_orchestrator_cls):
        """测试客户端缓存（多次调用返回同一实例）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch("meetgrow_skill.core.agent.OpenAI") as mock_openai_cls:
            mock_openai_cls.return_value = MagicMock()
            client1 = agent._get_client()
            client2 = agent._get_client()
            # OpenAI 只被实例化一次
            self.assertEqual(mock_openai_cls.call_count, 1)
            self.assertIs(client1, client2)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_client_no_api_key(self, mock_orchestrator_cls):
        """测试无 API Key 时使用 placeholder"""
        from meetgrow_skill.config import AgentConfig
        config = AgentConfig(api_base_url="http://test:11434/v1")
        from meetgrow_skill.core.agent import MeetGrowAgent

        mock_orchestrator_cls.return_value = MagicMock()
        agent = MeetGrowAgent(config=config)

        with patch("meetgrow_skill.core.agent.OpenAI") as mock_openai_cls:
            mock_openai_cls.return_value = MagicMock()
            agent._get_client()
            call_kwargs = mock_openai_cls.call_args[1]
            self.assertEqual(call_kwargs["api_key"], "placeholder")


class TestAgentCallLLM(unittest.TestCase):
    """测试 LLM 调用"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
            temperature=0.7,
            max_tokens=2048,
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_call_llm(self, mock_orchestrator_cls):
        """测试 LLM 调用"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            # Mock 响应
            mock_response = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response

            messages = [{"role": "user", "content": "hello"}]
            tools = [{"type": "function", "function": {"name": "test"}}]

            result = agent._call_llm(messages, tools)

            # 验证调用
            mock_client.chat.completions.create.assert_called_once_with(
                model="qwen3.6-35b-a3b",
                messages=messages,
                tools=tools,
                temperature=0.7,
                max_tokens=2048,
            )
            self.assertEqual(result, mock_response)


class TestAgentGetToolDefs(unittest.TestCase):
    """测试工具定义获取"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig()

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_tool_defs(self, mock_orchestrator_cls):
        """测试获取工具定义列表"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)
        tool_defs = agent._get_tool_defs()

        self.assertIsInstance(tool_defs, list)
        self.assertEqual(len(tool_defs), 6)
        for tool_def in tool_defs:
            self.assertEqual(tool_def["type"], "function")
            self.assertIn("function", tool_def)
            self.assertIn("name", tool_def["function"])
            self.assertIn("description", tool_def["function"])
            self.assertIn("parameters", tool_def["function"])


class TestAgentProcessNoToolCalls(unittest.TestCase):
    """测试 Agent 处理流程（无工具调用场景）"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_no_tool_calls(self, mock_orchestrator_cls):
        """测试 LLM 没有选择工具时的处理"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            # Mock 返回：没有 tool_calls（LLM 直接回答）
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "好的，我明白了。"
            mock_call_llm.return_value = mock_response

            result = agent.process("帮我整理一下会议纪要")

            self.assertEqual(result, "好的，我明白了。")
            self.assertEqual(mock_call_llm.call_count, 1)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_empty_input(self, mock_orchestrator_cls):
        """测试空输入处理"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "请输入内容"
            mock_call_llm.return_value = mock_response

            result = agent.process("")
            self.assertEqual(result, "请输入内容")


class TestAgentProcessWithToolCalls(unittest.TestCase):
    """测试 Agent 处理流程（有工具调用场景）"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_single_tool_call(self, mock_orchestrator_cls):
        """测试单个工具调用的完整流程"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            # 第一轮：LLM 选择工具
            mock_tc = MagicMock()
            mock_tc.id = "call_001"
            mock_tc.function.name = "ocr_business_card"
            mock_tc.function.arguments = '{"image_path": "/path/to/card.jpg"}'

            mock_msg = MagicMock()
            mock_msg.tool_calls = [mock_tc]
            mock_msg.content = None

            mock_call_1 = MagicMock()
            mock_call_1.choices = [MagicMock()]
            mock_call_1.choices[0].message = mock_msg

            # 第二轮：LLM 基于工具结果生成回复
            mock_call_2 = MagicMock()
            mock_call_2.choices = [MagicMock()]
            mock_call_2.choices[0].message.content = "识别结果：张三，XX公司，13800000000"
            mock_call_2.choices[0].message.tool_calls = None

            mock_call_llm.side_effect = [mock_call_1, mock_call_2]

            result = agent.process("请识别这张名片")

            # 验证：调用两次 LLM
            self.assertEqual(mock_call_llm.call_count, 2)
            # 第一次调用有工具定义（call_args[0] 是位置参数 tuple）
            first_tools = mock_call_llm.call_args_list[0][0][1]
            self.assertEqual(len(first_tools), 6)
            # 第二次调用没有工具定义（tools=[]，作为 keyword arg）
            second_tools = mock_call_llm.call_args_list[1][1].get("tools")
            self.assertEqual(second_tools, [])
            # 验证结果
            self.assertEqual(result, "识别结果：张三，XX公司，13800000000")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_multiple_tool_calls(self, mock_orchestrator_cls):
        """测试多个工具调用的流程（如：OCR + TTS）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            # 第一轮：LLM 选择两个工具
            tc1 = MagicMock()
            tc1.id = "call_001"
            tc1.function.name = "ocr_business_card"
            tc1.function.arguments = '{"image_path": "/card.jpg"}'
            tc2 = MagicMock()
            tc2.id = "call_002"
            tc2.function.name = "text_to_speech"
            tc2.function.arguments = '{"text": "识别成功"}'

            mock_msg = MagicMock()
            mock_msg.tool_calls = [tc1, tc2]
            mock_msg.content = None

            mock_call_1 = MagicMock()
            mock_call_1.choices = [MagicMock()]
            mock_call_1.choices[0].message = mock_msg

            # 第二轮
            mock_call_2 = MagicMock()
            mock_call_2.choices = [MagicMock()]
            mock_call_2.choices[0].message.content = "完成 OCR 和语音播报"
            mock_call_2.choices[0].message.tool_calls = None

            mock_call_llm.side_effect = [mock_call_1, mock_call_2]

            result = agent.process("请识别名片并语音播报结果")

            self.assertEqual(mock_call_llm.call_count, 2)
            self.assertEqual(result, "完成 OCR 和语音播报")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_tool_error(self, mock_orchestrator_cls):
        """测试工具执行失败时 Agent 的处理"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            tc = MagicMock()
            tc.id = "call_001"
            tc.function.name = "ocr_business_card"
            tc.function.arguments = '{"image_path": "/nonexistent.jpg"}'

            mock_msg = MagicMock()
            mock_msg.tool_calls = [tc]
            mock_msg.content = None

            mock_call_1 = MagicMock()
            mock_call_1.choices = [MagicMock()]
            mock_call_1.choices[0].message = mock_msg

            # 工具执行返回错误，LLM 据此生成回复
            mock_call_2 = MagicMock()
            mock_call_2.choices = [MagicMock()]
            mock_call_2.choices[0].message.content = "文件不存在，请检查路径"
            mock_call_2.choices[0].message.tool_calls = None

            mock_call_llm.side_effect = [mock_call_1, mock_call_2]

            result = agent.process("请识别这张名片")
            self.assertIn("文件不存在", result)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_with_images(self, mock_orchestrator_cls):
        """测试带图片附件的输入"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "已处理"
            mock_call_llm.return_value = mock_response

            result = agent.process("处理图片", images=["/path/to/a.jpg", "/path/to/b.jpg"])

            # 验证消息中包含附件信息
            first_call = mock_call_llm.call_args_list[0]
            user_content = first_call[0][0][1]["content"]
            self.assertIn("附件 2 个图片", user_content)
            self.assertIn("a.jpg", user_content)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_with_audio(self, mock_orchestrator_cls):
        """测试带音频附件的输入"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "已处理"
            mock_call_llm.return_value = mock_response

            result = agent.process("处理音频", audio_files=["/path/to/audio.mp3"])

            first_call = mock_call_llm.call_args_list[0]
            user_content = first_call[0][0][1]["content"]
            self.assertIn("附件 1 个音频", user_content)
            self.assertIn("audio.mp3", user_content)


class TestAgentProcessToolExecution(unittest.TestCase):
    """测试 Agent 中 orchestrator.execute 的实际调用"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_calls_orchestrator_execute(self, mock_orchestrator_cls):
        """测试 process 正确调用 orchestrator.execute"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator = MagicMock()
        mock_orchestrator_cls.return_value = mock_orchestrator

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_call_1 = MagicMock()
            mock_call_1.choices = [MagicMock()]
            tc = MagicMock()
            tc.id = "call_001"
            tc.function.name = "generate_meeting_minutes"
            tc.function.arguments = '{"transcript": "会议内容"}'
            mock_call_1.choices[0].message.tool_calls = [tc]

            mock_call_2 = MagicMock()
            mock_call_2.choices = [MagicMock()]
            mock_call_2.choices[0].message.content = "纪要已生成"
            mock_call_llm.side_effect = [mock_call_1, mock_call_2]

            result = agent.process("生成会议纪要")

            # 验证 orchestrator.execute 被调用
            mock_orchestrator.execute.assert_called_once_with(
                "generate_meeting_minutes",
                {"transcript": "会议内容"}
            )
            self.assertEqual(result, "纪要已生成")


class TestAgentShortcutMethods(unittest.TestCase):
    """测试 Agent 快捷方法"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_card_ocr(self, mock_orchestrator_cls):
        """测试名片 OCR 快捷方法"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "process") as mock_process:
            mock_process.return_value = "Card result"
            result = agent.process_card_ocr("/path/to/card.jpg")

            # 验证 process 被调用并传递正确参数
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            self.assertIn("请识别这张名片: /path/to/card.jpg", call_args[1]["user_input"])
            self.assertIn("/path/to/card.jpg", call_args[1]["images"])

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_meeting_basic(self, mock_orchestrator_cls):
        """测试会议转纪要快捷方法（无标题）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "process") as mock_process:
            mock_process.return_value = "Meeting result"
            result = agent.process_meeting("/path/to/audio.mp3")

            mock_process.assert_called_once()
            call_args = mock_process.call_args
            self.assertIn("请将这份会议录音转写成纪要: /path/to/audio.mp3",
                          call_args[1]["user_input"])
            self.assertIn("/path/to/audio.mp3", call_args[1]["audio_files"])

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_meeting_with_title(self, mock_orchestrator_cls):
        """测试会议转纪要快捷方法（带标题）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "process") as mock_process:
            mock_process.return_value = "Meeting result"
            result = agent.process_meeting("/path/to/audio.mp3", title="Q2招商会议")

            mock_process.assert_called_once()
            call_args = mock_process.call_args
            self.assertIn("会议标题: Q2招商会议", call_args[1]["user_input"])
            self.assertIn("/path/to/audio.mp3", call_args[1]["audio_files"])


class TestAgentSystemPrompt(unittest.TestCase):
    """测试 Agent 系统提示词"""

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_system_prompt_includes_tool_descriptions(self, mock_orchestrator_cls):
        """测试系统提示词包含所有工具描述"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        prompt = agent.system_prompt

        # 应包含所有 6 个工具的描述
        self.assertIn("ocr_business_card", prompt)
        self.assertIn("speech_to_text", prompt)
        self.assertIn("text_to_speech", prompt)
        self.assertIn("generate_meeting_minutes", prompt)
        self.assertIn("smart_archive", prompt)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_system_prompt_structure(self, mock_orchestrator_cls):
        """测试系统提示词结构完整"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        prompt = agent.system_prompt

        self.assertIn("理解意图", prompt)
        self.assertIn("选择工具", prompt)
        self.assertIn("编排执行", prompt)
        self.assertIn("整合结果", prompt)
        self.assertIn("隐私", prompt)
        self.assertIn("中文", prompt)


class TestAgentEdgeCases(unittest.TestCase):
    """测试 Agent 边界情况"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_with_none_images(self, mock_orchestrator_cls):
        """测试 images=None 时不报错"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "OK"
            mock_call_llm.return_value = mock_response

            # images=None 应该不附加任何附件信息
            result = agent.process("test", images=None, audio_files=None)
            self.assertEqual(result, "OK")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_with_empty_lists(self, mock_orchestrator_cls):
        """测试空列表参数"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].message.content = "OK"
            mock_call_llm.return_value = mock_response

            # 空列表不应触发附件附加
            result = agent.process("test", images=[], audio_files=[])
            self.assertEqual(result, "OK")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_card_ocr_return_type(self, mock_orchestrator_cls):
        """测试 process_card_ocr 返回值类型"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "process") as mock_process:
            mock_process.return_value = "Result"
            result = agent.process_card_ocr("/test.jpg")
            self.assertIsInstance(result, str)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_process_meeting_return_type(self, mock_orchestrator_cls):
        """测试 process_meeting 返回值类型"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "process") as mock_process:
            mock_process.return_value = "Result"
            result = agent.process_meeting("/test.mp3", title="Test")
            self.assertIsInstance(result, str)


class TestAgentIntegrationWithOrchestrator(unittest.TestCase):
    """测试 Agent 与编排器的集成"""

    def setUp(self):
        from meetgrow_skill.config import AgentConfig
        self.config = AgentConfig(
            api_base_url="http://test-api:11434/v1",
            api_key="test-key",
            model_name="qwen3.6-35b-a3b",
        )

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_tool_result_passed_to_llm(self, mock_orchestrator_cls):
        """测试工具结果正确传递给第二轮 LLM"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator = MagicMock()
        mock_orchestrator_cls.return_value = mock_orchestrator

        agent = MeetGrowAgent(config=self.config)

        with patch.object(agent, "_call_llm") as mock_call_llm:
            mock_call_1 = MagicMock()
            mock_call_1.choices = [MagicMock()]
            tc = MagicMock()
            tc.id = "call_001"
            tc.function.name = "ocr_business_card"
            tc.function.arguments = '{"image_path": "/card.jpg"}'
            mock_call_1.choices[0].message.tool_calls = [tc]

            mock_call_2 = MagicMock()
            mock_call_2.choices = [MagicMock()]
            mock_call_2.choices[0].message.content = "OCR 结果：张三"
            mock_call_llm.side_effect = [mock_call_1, mock_call_2]

            mock_orchestrator.execute.return_value = {
                "status": "success",
                "name": "张三",
                "company": "XX公司",
            }

            result = agent.process("识别名片")

            # 验证第二轮 LLM 调用中包含了工具结果
            second_call = mock_call_llm.call_args_list[1]
            messages = second_call[0][0]
            # 找到 tool 角色的消息
            tool_messages = [m for m in messages if m.get("role") == "tool"]
            self.assertEqual(len(tool_messages), 1)
            content = json.loads(tool_messages[0]["content"])
            self.assertEqual(content["name"], "张三")
            self.assertEqual(content["company"], "XX公司")


class TestAgentSkillDefinition(unittest.TestCase):
    """测试 Agent 中的 Skill 定义"""

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_skill_tools_accessible(self, mock_orchestrator_cls):
        """测试 Agent 可直接访问所有工具定义"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()

        for tool in agent.skill.tools:
            self.assertIsNotNone(tool.name)
            self.assertIsNotNone(tool.description)
            self.assertIsNotNone(tool.parameters)
            fmt = tool.to_openai_format()
            self.assertEqual(fmt["type"], "function")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_tool_descriptions(self, mock_orchestrator_cls):
        """测试获取工具描述列表"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        descriptions = agent.skill.get_tool_descriptions()

        self.assertIsInstance(descriptions, list)
        self.assertEqual(len(descriptions), 6)
        for desc in descriptions:
            self.assertIsInstance(desc, str)
            self.assertTrue(len(desc) > 10)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_all_tools_dict(self, mock_orchestrator_cls):
        """测试获取所有工具字典（用 tools list 替代）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        tools_dict = {tool.name: tool for tool in agent.skill.tools}

        self.assertIsInstance(tools_dict, dict)
        self.assertEqual(len(tools_dict), 6)
        self.assertIn("ocr_business_card", tools_dict)
        self.assertIn("speech_to_text", tools_dict)

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_tool_by_name(self, mock_orchestrator_cls):
        """测试按名称获取工具（通过列表遍历）"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        tool = next((t for t in agent.skill.tools if t.name == "text_to_speech"), None)
        self.assertIsNotNone(tool)
        self.assertEqual(tool.name, "text_to_speech")

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_tool_not_found(self, mock_orchestrator_cls):
        """测试获取不存在的工具"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        tool = next((t for t in agent.skill.tools if t.name == "nonexistent_tool"), None)
        self.assertIsNone(tool)


class TestAgentToolDescriptionMethods(unittest.TestCase):
    """测试工具描述辅助方法"""

    @patch("meetgrow_skill.core.agent.ToolOrchestrator")
    def test_get_tool_descriptions_format(self, mock_orchestrator_cls):
        """测试工具描述格式"""
        from meetgrow_skill.core.agent import MeetGrowAgent
        mock_orchestrator_cls.return_value = MagicMock()

        agent = MeetGrowAgent()
        descriptions = agent.skill.get_tool_descriptions()

        for desc in descriptions:
            # 每个描述应包含工具名和功能
            self.assertIn(":", desc)


if __name__ == "__main__":
    unittest.main()
