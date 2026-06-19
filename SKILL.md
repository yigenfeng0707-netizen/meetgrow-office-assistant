---
name: meetgrow-office-assistant
description: >
  会展招商办公提效 Agent Skill。基于 35B 以下小模型（Qwen3.6-35B-A3B）作为 Agent 大脑，
  驱动本地 OCR、ASR、TTS 工具，实现名片识别、会议纪要生成、语音播报、资料归档等办公自动化任务。
  适用于 Intel AI PC，数据不出机，支持离线运行。
license: MIT
compatibility: >
  为 Intel AI PC 设计，支持 Windows 11 / macOS / Linux。
  需要 Python 3.10+，推荐 Intel Core Ultra 处理器。
  首次运行需联网下载模型，之后可离线使用。
metadata:
  author: WinClaw
  version: "1.0.0"
  tags: ["agent", "ocr", "asr", "tts", "office", "intel-ai-pc", "meetgrow"]
  competition: "AI PC Agent Skills 征文大赛"
  article_url: "https://www.modelscope.cn/notes/{PLEASE_REPLACE_WITH_REAL_ARTICLE_ID}"
  github_repo: "https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant"
  release: "https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant/releases/tag/v1.0.0"
---

# MeetGrow Office Assistant - AI PC Agent Skill

## 概述

MeetGrow Office Assistant 是一个运行在 **Intel AI PC** 上的本地化办公智能体 Skill，聚焦会展招商场景：

- **名片 OCR 识别**：扫描名片，自动提取姓名、公司、职位、电话、邮箱
- **会议录音转纪要**：语音转文字后自动生成议程、摘要、决策、待办
- **语音播报提醒**：将待办事项、会议纪要转为语音
- **资料智能归档**：按日期/类别自动整理名片、文档、音频

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     MeetGrow Office Assistant                │
├─────────────────────────────────────────────────────────────┤
│  Agent Brain                                                 │
│  Qwen3.6-35B-A3B via ModelScope API                          │
│  ├── 意图识别                                                │
│  ├── 工具规划                                                │
│  └── 结果整合                                                │
├─────────────────────────────────────────────────────────────┤
│  Local Tools (本地运行，数据不出机)                           │
│  ├── OCRTool    → PaddleOCR 名片/文档识别                    │
│  ├── ASRTool    → FunASR 语音转文字                          │
│  ├── TTSTool    → edge-tts 文字转语音                        │
│  └── DocTool    → 会议纪要生成 / 智能归档                    │
├─────────────────────────────────────────────────────────────┤
│  Service Layer (常驻服务，推荐部署方式)                       │
│  ├── server.py  → FastAPI 服务，工具常驻内存                  │
│  └── client.py  → Python / CLI 客户端                        │
└─────────────────────────────────────────────────────────────┘
```

## 安装

### 1. 克隆项目并创建环境

```bash
git clone <your-repo-url>
cd meetgrow-agent-skill
conda create -n meetgrow python=3.11 -y
conda activate meetgrow
pip install -r requirements.txt
```

### 2. 下载本地模型

```bash
python scripts/download_models.py
```

模型清单：

| 工具 | 模型 | 下载来源 | 本地路径 |
|------|------|----------|----------|
| OCR | PP-OCRv5 | 首次运行自动下载 | `~/.paddlex/` |
| ASR | paraformer-zh | [ModelScope](https://www.modelscope.cn/models/iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/summary) | `models/funasr/paraformer-zh/` |
| ASR | fsmn-vad | [ModelScope](https://www.modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/summary) | `models/funasr/fsmn-vad/` |
| ASR | ct-punc | [ModelScope](https://www.modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large/summary) | `models/funasr/ct-punc/` |
| TTS | edge-tts | 在线服务，无需本地模型 | - |

### 3. 配置 API Key

编辑 `~/meetgrow_data/config.yaml`：

```yaml
api_base_url: "https://api-inference.modelscope.cn/v1"
api_key: "your-modelscope-api-key"
model_name: "qwen3.6-35b-a3b"
```

## 使用方式

### 方式一：命令行（CLI）

```bash
# 初始化
python -m meetgrow_skill init

# 名片识别
python -m meetgrow_skill ocr examples/test_card.jpg

# 语音转文字
python -m meetgrow_skill asr meeting_recording.wav

# 文本转语音
python -m meetgrow_skill tts "今天的会议有3项待办事项" --voice 小晓

# Agent 交互
python -m meetgrow_skill agent "识别这张名片并生成联系人档案" --image card.jpg
```

### 方式二：常驻服务（推荐）

```bash
# 启动服务
python server/server.py

# 客户端调用
python server/client.py ocr examples/test_card.jpg
python server/client.py asr meeting_recording.wav
python server/client.py tts "会议提醒：下午3点项目复盘"
```

### 方式三：Python API

```python
from meetgrow_skill import MeetGrowAgent

agent = MeetGrowAgent()
result = agent.process("扫描这份会议资料，提取关键信息并生成纪要")
print(result)
```

## 工具清单

| 工具名 | 功能 | 本地依赖 |
|--------|------|----------|
| `ocr_business_card` | 名片识别 | PaddleOCR |
| `ocr_document` | 文档/票据 OCR | PaddleOCR |
| `speech_to_text` | 语音转文字 | FunASR |
| `text_to_speech` | 文字转语音 | edge-tts |
| `generate_meeting_minutes` | 会议纪要生成 | Agent + DocTool |
| `smart_archive` | 智能归档 | DocTool |

## 示例脚本

项目 `examples/` 目录提供完整示例：

- `demo_card_ocr.py` - 名片识别完整流程
- `demo_meeting_minutes.py` - 录音转纪要
- `demo_complete_agent.py` - 完整 Agent 交互
- `demo_voice_assistant.py` - 语音助手

## 测试

```bash
# 运行全部测试
python -m unittest discover tests -v

# 验证 SKILL 格式
npx skills-ref validate skills/meetgrow-office-assistant
```

## 模型下载详情

### OCR - PaddleOCR

PaddleOCR 模型会在首次调用时自动下载到 `~/.paddlex/`。也可手动下载：

- 模型仓库：[PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- 安装命令：`pip install paddlepaddle paddleocr`

### ASR - FunASR

```bash
python scripts/download_models.py --model-dir models/funasr
```

下载脚本会自动从 ModelScope 拉取：

- `iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- `iic/speech_fsmn_vad_zh-cn-16k-common-pytorch`
- `iic/punc_ct-transformer_cn-en-common-vocab471067-large`

### TTS - edge-tts

edge-tts 使用微软 Edge 在线 TTS 服务，无需本地模型：

```bash
pip install edge-tts
```

## 参考资料

- `docs/tech_article.md` - 完整技术文章
- `README.md` - 项目说明
- `examples/` - 示例代码
- `tests/` - 单元测试

## 作者

- 作者：WinClaw
- 作品：MeetGrow Office Assistant
- 研习社文章：[请替换为真实文章 URL]
