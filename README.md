# 🤖 MeetGrow AI PC Agent Skill

> **英特尔 × 魔搭社区：AI PC Agent Skills 征文活动参赛作品**
> 
> 基于 Qwen3.6-35B-A3B 小模型，驱动本地 AI 工具（OCR / ASR / TTS），赋能会展招商办公提效场景
> 
> **研习社文章**：[待替换为正式文章 URL，发布后将自动更新](https://www.modelscope.cn/notes/{PLEASE_REPLACE_WITH_REAL_ARTICLE_ID})
>
> **GitHub 仓库**：[yigenfeng0707-netizen/meetgrow-office-assistant](https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant)
>
> **提交包下载**：[Release v1.0.0](https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant/releases/tag/v1.0.0)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Test](https://img.shields.io/badge/Tests-186%2F186-passing-brightgreen.svg)](tests/)
[![ModelScope](https://img.shields.io/badge/ModelScope-Skill-orange.svg)](https://modelscope.cn)
[![AI PC](https://img.shields.io/badge/AI%20PC-Compatible-brightblue.svg)](https://modelscope.cn/brand/view/AI_PC)

---

## 📋 项目概述

MeetGrow AI PC Agent Skill 是一个运行在 Intel AI PC 上的本地化智能办公助手。它利用 **35B 参数以下的小模型** 作为 Agent 大脑，调度本地 OCR、ASR、TTS 等工具，实现会展招商场景中的智能办公自动化。

### 核心理念

```
Hybrid AI 架构 = 云端模型大脑 + 本地工具双手
```

- **云端大脑**：Qwen3.6-35B-A3B 负责意图识别、任务规划、工具调度
- **本地双手**：OCR / ASR / TTS 等工具在 AI PC 本地运行，确保数据隐私
- **混合优势**：云端智能决策 + 本地隐私保护 = 企业级 AI 办公助手

### 核心能力

| 能力 | 工具 | 模型/框架 | 场景 |
|------|------|-----------|------|
| 📄 **智能 OCR** | `ocr_tool.py` | PaddleOCR (PP-OCRv5) | 名片识别、会议资料扫描、发票提取 |
| 🎙️ **语音转写** | `asr_tool.py` | FunASR (Paraformer) | 会议录音转文字、语音指令识别 |
| 🔊 **语音合成** | `tts_tool.py` | edge-tts (微软) | 会议纪要播报、待办事项语音提醒 |
| 📊 **文档处理** | `doc_tool.py` | 自研引擎 | 会议纪要生成、智能归档 |

---

## 🏗️ 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────┐
│                   MeetGrow AI PC Agent                │
├─────────────────────────────────────────────────────┤
│  Agent Brain (Qwen3.6-35B-A3B via API)              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │ Intent   │ │Tool      │ │ Memory   │            │
│  │ Router   │ │ Planner  │ │ Manager  │            │
│  └──────────┘ └──────────┘ └──────────┘            │
├─────────────────────────────────────────────────────┤
│  Local Tools (运行在本地 AI PC)                      │
│  ┌────────┐ ┌───────┐ ┌────────┐ ┌─────────┐      │
│  │ Paddle │ │ FunASR│ │edge-tts│ │ DocEng  │      │
│  │  OCR   │ │       │ │        │ │         │      │
│  └────────┘ └───────┘ └────────┘ └─────────┘      │
├─────────────────────────────────────────────────────┤
│  MeetGrow AI 集成场景                                 │
│  🎫 会议签到 → 名片OCR → 自动建档案                  │
│  📝 会议录音 → ASR转写 → 自动生成纪要                │
│  📊 资料扫描 → OCR提取 → 结构化归档                  │
│  📢 待办播报 → TTS语音 → 智能提醒                    │
└─────────────────────────────────────────────────────┘
```

### 模块说明

```
meetgrow_skill/
├── config.py          # Agent 配置管理（单例模式，支持自定义配置）
├── skill.py           # Skill 定义与 OpenAI 格式转换
├── core/
│   ├── agent.py       # MeetGrowAgent - Agent 大脑核心
│   ├── memory.py      # ConversationMemory - 对话记忆管理
│   └── orchestrator.py # ToolOrchestrator - 工具编排引擎
└── tools/
    ├── base.py        # BaseTool - 抽象工具基类
    ├── ocr_tool.py    # PaddleOCR 名片/文档识别
    ├── asr_tool.py    # FunASR 语音转文字
    ├── tts_tool.py    # edge-tts 文字转语音
    └── doc_tool.py    # 文档处理（会议纪要/智能归档）
```

---

## 📦 安装

### 系统要求

- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.11+
- **硬件**: Intel Core Ultra (推荐), 8GB+ RAM
- **网络**: 首次运行需联网下载模型，后续可离线使用

### 快速安装

```bash
# 1. 创建 conda 环境
conda create -n meetgrow python=3.11 -y
conda activate meetgrow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 下载本地模型（OCR / ASR）
python scripts/download_models.py

# 4. 初始化 MeetGrow 环境
python -m meetgrow_skill init

# 5. 运行
python -m meetgrow_skill --help
```

### 常驻服务部署（推荐）

避免每次调用重新加载模型，适合生产环境：

```bash
# 启动服务
python server/server.py

# 客户端调用
python server/client.py ocr examples/test_card.jpg
python server/client.py asr meeting_recording.wav
python server/client.py tts "下午3点项目复盘" --voice 小晓
```

### 可选依赖

```bash
# 仅使用 OCR（不依赖 ASR/TTS）
pip install paddleocr

# 使用 ASR（语音转写）
pip install funasr torchaudio

# 使用 TTS（语音合成）
pip install edge-tts
```

---

## 🚀 快速开始

### 场景 1：名片 OCR 识别

```bash
python -m meetgrow_skill ocr card --image business_card.jpg
```

输出结构化联系人信息：
```json
{
  "name": "张三",
  "company": "XX科技有限公司",
  "title": "采购总监",
  "phone": "138-0000-0000",
  "email": "zhangsan@example.com"
}
```

### 场景 2：会议录音转纪要

```bash
python -m meetgrow_skill meeting --audio meeting_recording.wav --summary
```

输出包含议程摘要、决策事项、待办清单。

### 场景 3：完整 Agent 交互

```python
from meetgrow_skill import MeetGrowAgent

agent = MeetGrowAgent()
result = agent.run("扫描这份会议资料，提取关键信息并生成纪要")
print(result)
```

### 场景 4：使用 Skill 定义

```python
from meetgrow_skill import get_skill_definition

skill = get_skill_definition()
print(f"Skill: {skill.metadata.name}")
print(f"Tools: {len(skill.tools)}")
for tool in skill.tools:
    print(f"  - {tool.function.name}: {tool.function.description[:50]}...")
```

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| 总代码行数 | ~3,500 行 |
| 工具数量 | 6 (OCR×2, ASR, TTS, Doc×2) |
| 测试用例 | 186 (100% 通过) |
| 核心模块 | 9 个 Python 模块 |
| 文档 | README + SKILL.md + 技术文章 |
| 提交包 | manifest.json + zip 打包 |

---

## 📖 技术文档

### 征文文章

- **魔搭研习社**: [用 35B 小模型构建端侧 AI 办公智能体](https://www.modelscope.cn/notes/{PLEASE_REPLACE_WITH_REAL_ARTICLE_ID})（发布后将替换为真实文章 URL）
- **CSDN**: [英特尔 AI PC Agent Skills 征文](https://inteldevkit.csdn.net/69f40f920a2f6a37c5a7228f.html)

### 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| **模型** | Qwen3.6-35B-A3B | 端侧 35B 参数混合专家模型，≤35B 约束 |
| **OCR** | PaddleOCR (PP-OCRv5) | 支持中英文/表格/票据识别 |
| **ASR** | FunASR (Paraformer) | 实时流式语音识别，支持中文 |
| **TTS** | edge-tts | 微软 Edge 浏览器免费 TTS 引擎 |
| **推理** | 本地 CPU / Intel Arc GPU | 支持 Intel 异构算力加速 |
| **部署** | 纯 Python | 零外部服务依赖，开箱即用 |

### API 参考

#### MeetGrowAgent

```python
class MeetGrowAgent:
    """MeetGrow AI Agent - 智能办公助手"""
    
    def __init__(self, config: AgentConfig = None):
        """初始化 Agent"""
    
    def run(self, user_input: str) -> dict:
        """执行 Agent 交互"""
    
    def get_tools(self) -> list:
        """获取所有可用工具"""
```

#### ToolOrchestrator

```python
class ToolOrchestrator:
    """工具编排引擎 - 链式执行工具"""
    
    def register_tool(self, tool: BaseTool):
        """注册工具"""
    
    def execute(self, tool_name: str, **kwargs) -> dict:
        """执行指定工具"""
    
    def execute_chain(self, chain: list) -> list:
        """链式执行"""
```

---

## 🧪 测试

### 运行测试

```bash
# 运行全部测试
python -m unittest discover tests -v

# 运行指定模块
python -m unittest tests.test_tts -v
```

### 测试结果

> 186 个测试全部通过，核心模块均有完整覆盖

| 模块 | 测试数 | 通过率 | 覆盖范围 |
|------|--------|--------|----------|
| test_config | 8 | 100% | 配置管理、默认值、工作目录 |
| test_skill | 15 | 100% | 元数据、6 工具定义、OpenAI 格式 |
| test_base | 3 | 100% | 抽象基类、继承、路径校验 |
| test_doc | 19 | 100% | 会议纪要、智能归档、错误处理 |
| test_memory | 15 | 100% | 消息管理、上下文持久化、会话清理 |
| test_ocr | 26 | 100% | 名片识别、通用识别、错误处理 |
| test_orchestrator | 5 | 100% | 工具注册、链式执行、状态管理 |
| test_asr | 6 | 100% | 语音转写、异常降级、Schema 验证 |
| test_tts | 15 | 100% | 语音合成、声音别名、输入校验 |
| test_integration | 18 | 100% | 端到端工作流、场景模拟、配置集成 |
| test_agent | 26 | 100% | Agent 初始化、工具调用、结果整合 |
| test_cli | 5 | 100% | 命令行入口、参数解析 |
| **合计** | **186** | **100% ✅** | **核心模块全覆盖** |

### 快速验证

```bash
# 全量测试（约 30 秒）
python -m unittest discover tests -v

# 只看集成测试
python -m unittest tests.test_integration -v

# 指定模块
python -m unittest tests.test_tts -v
```

---

## 📦 发布与提交

### 生成提交包

```bash
# 生成 Skill 提交包（含代码、文档、测试）
python publish_skill.py

# 输出:
#   dist/manifest.json          # 魔搭提交 Manifest
#   dist/meetgrow_skill.json    # Skill 定义文件
#   dist/meetgrow-skill-*.zip   # 完整提交包
```

### 提交到魔搭

1. 访问 [魔搭 Skills 中心](https://modelscope.cn)
2. 上传 `dist/meetgrow-skill-*.zip`
3. 添加自定义标签 **"AIPC"**
4. 在魔搭研习社发表技术文章，添加标签 **"Intel AI PC"**

---

## 🛠️ 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `ffmpeg is not installed` | 音频处理需要 ffmpeg | `conda install -c conda-forge ffmpeg` |
| FunASR 模型下载失败 | 网络问题 / repo_id 格式 | 确保网络畅通，手动下载放 `models/funasr/` |
| PaddleOCR 加载慢 | 首次下载模型 | 模型缓存于 `~/.paddlex/`，后续离线可用 |
| TTS 合成超时 | edge-tts 网络波动 | 重试或检查网络，默认 15s 超时 |
| `Invalid model id` | API 模型 ID 不匹配 | 检查 config.py 中 model_name 配置 |

## 🤝 贡献指南

### 开发环境搭建

```bash
# 1. 克隆项目
git clone <repo-url>
cd meetgrow-agent-skill

# 2. 创建环境
conda create -n meetgrow python=3.11 -y
conda activate meetgrow
pip install -r requirements.txt

# 3. 安装开发依赖
pip install pytest coverage

# 4. 运行测试
python -m unittest discover tests -v

# 5. 生成覆盖率报告
pip install coverage
coverage run -m unittest discover tests
coverage report -m
coverage html  # 生成 HTML 报告
```

### 提交规范

1. 每个功能模块有对应测试
2. 测试覆盖率 ≥ 80%
3. 遵循 PEP 8 代码风格
4. 中文注释 + 类型标注
5. 提交前运行完整测试套件

---

## 📄 许可证

MIT License

---

*Built with ❤️ by WinClaw for Intel × ModelScope AI PC Agent Skills Competition*
