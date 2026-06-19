---
name: meetgrow-office-assistant
description: >
  会展招商办公提效 Agent Skill。基于 35B 以下小模型作为 Agent 大脑，
  驱动本地 OCR、ASR、TTS 工具，实现名片识别、会议纪要生成、语音播报、资料归档等办公自动化任务。
license: MIT
compatibility: >
  为 Intel AI PC 设计，支持 Windows 11 / macOS / Linux，需要 Python 3.10+。
metadata:
  author: WinClaw
  version: "1.0.0"
  tags: ["agent", "ocr", "asr", "tts", "office", "intel-ai-pc", "meetgrow"]
---

# MeetGrow Office Assistant

## 用途

当用户需要处理会展招商场景中的办公任务时，使用本 Skill：

- 识别名片图片并提取联系人信息
- 将会议录音转写为文字并生成纪要
- 把文本转换为语音播报
- 自动归档名片、文档、音频资料

## 使用步骤

### 1. 环境准备

```bash
pip install -r requirements.txt
python scripts/download_models.py
```

### 2. 启动本地服务（推荐）

常驻服务会保持 OCR/ASR/TTS 工具在内存中，避免每次调用重新初始化：

```bash
python server/server.py
```

### 3. 调用工具

```bash
# 名片识别
python skills/meetgrow-office-assistant/scripts/card_ocr.py examples/test_card.jpg

# 会议录音转纪要
python skills/meetgrow-office-assistant/scripts/meeting_minutes.py meeting.wav

# 语音播报
python skills/meetgrow-office-assistant/scripts/voice_assistant.py "下午3点项目复盘"
```

## 注意事项

- 首次运行会下载 PaddleOCR / FunASR 模型，需要联网
- OCR / ASR 计算在本地完成，数据不上传云端
- Agent 大脑通过 ModelScope API 调用 Qwen3.6-35B-A3B，需配置 API Key

## 参考

- `docs/tech_article.md` - 技术文章
- `README.md` - 项目说明
- `SKILL.md`（项目根目录）- 大赛提交文档
