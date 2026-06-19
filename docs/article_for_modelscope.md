# MeetGrow Office Assistant：用 35B 小模型打造 AI PC 端侧办公智能体

> **英特尔 × 魔搭社区 AI PC Agent Skills 征文活动参赛作品**
> 作者：WinClaw | 作品：MeetGrow Office Assistant

## 一、为什么做这个项目？

会展招商是一个信息密度极高的场景：名片、会议录音、活动资料、待办提醒……传统方式下，这些工作大量依赖人工录入和整理。我们希望在 **Intel AI PC** 上构建一个本地化、可复用的办公智能体，让 AI 在保护隐私的前提下，自动完成这些重复劳动。

核心设计目标：

- **数据不出机**：名片、录音等敏感信息本地处理
- **小模型驱动大脑**：使用 ≤35B 参数模型做决策，降低本地硬件压力
- **本地工具真实落地**：OCR、ASR、TTS 等工具在本地真实运行
- **可复用 Skill**：封装为可被 Agent 调用的标准化技能

## 二、技术架构：云端大脑 + 本地双手

我们采用 **Hybrid AI** 架构：

- **云端大脑**：Qwen3.6-35B-A3B（通过 ModelScope API 调用）负责意图识别、工具调度、结果整合
- **本地双手**：PaddleOCR、FunASR、edge-tts 在本地 AI PC 上执行

```
用户输入 → Agent 大脑（Qwen3.6-35B-A3B）→ 本地工具 → 结果返回
```

这种分工的好处：

| 维度 | 纯云端方案 | Hybrid AI 方案 |
|------|-----------|----------------|
| 隐私 | 数据上传 | 敏感数据本地处理 |
| 成本 | 按次计费 | 本地零成本 |
| 延迟 | 200-500ms | 50-200ms |
| 离线 | 不可 | 本地工具可离线 |

## 三、本地工具链如何实现

### 3.1 OCR - 名片识别

使用 **PaddleOCR (PP-OCRv5)**，对名片图片进行文字识别，再用正则和启发式规则提取：

- 姓名
- 公司
- 职位
- 电话
- 邮箱

代码位置：`meetgrow_skill/tools/ocr_tool.py`

### 3.2 ASR - 会议录音转写

使用 **FunASR (Paraformer)** 从 ModelScope 下载中文语音识别模型：

- `speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`
- `speech_fsmn_vad_zh-cn-16k-common-pytorch`
- `punc_ct-transformer_cn-en-common-vocab471067-large`

代码位置：`meetgrow_skill/tools/asr_tool.py`

### 3.3 TTS - 语音播报

使用 **edge-tts**，无需 API Key，支持多音色中文语音合成。

代码位置：`meetgrow_skill/tools/tts_tool.py`

### 3.4 常驻服务（推荐部署方式）

为避免每次调用重复加载模型，我们提供 FastAPI 常驻服务：

```bash
python server/server.py
python server/client.py ocr examples/test_card.jpg
```

服务启动后，OCR/ASR/TTS 工具实例常驻内存，响应更快。

## 四、模型下载与安装

```bash
conda create -n meetgrow python=3.11 -y
conda activate meetgrow
pip install -r requirements.txt

# 下载 ASR 模型
python scripts/download_models.py

# 初始化环境
python -m meetgrow_skill init
```

模型下载链接：

- PaddleOCR：首次调用自动下载，仓库 [PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
- Paraformer：[ModelScope 链接](https://www.modelscope.cn/models/iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch/summary)
- FSMN-VAD：[ModelScope 链接](https://www.modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch/summary)
- CT-Punc：[ModelScope 链接](https://www.modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large/summary)

## 五、典型场景演示

### 场景 1：名片识别建档

```bash
python -m meetgrow_skill ocr examples/test_card.jpg
```

输出结构化联系人 JSON。

### 场景 2：会议录音转纪要

```bash
python skills/meetgrow-office-assistant/scripts/meeting_minutes.py meeting.wav "Q2 招商推进会"
```

先 ASR 转写，再调用 Agent 生成议程、摘要、决策、待办。

### 场景 3：待办语音播报

```bash
python -m meetgrow_skill tts "下午3点项目复盘，请准时参加" --voice 小晓
```

## 六、Skill 封装

本项目同时提供两份 SKILL.md：

- 根目录 `SKILL.md`：大赛提交文档
- `skills/meetgrow-office-assistant/SKILL.md`：符合 Agent Skills 标准格式

工具定义在 `meetgrow_skill/skill.py` 中，包含 6 个工具：

- `ocr_business_card`
- `ocr_document`
- `speech_to_text`
- `text_to_speech`
- `generate_meeting_minutes`
- `smart_archive`

## 七、测试与验证

```bash
python -m unittest discover tests -v
```

项目包含完整的单元测试和集成测试，覆盖 OCR、ASR、TTS、编排器、Agent 等模块。

## 八、总结

MeetGrow Office Assistant 通过 **小模型决策 + 本地工具执行** 的 Hybrid AI 架构，在 Intel AI PC 上实现了会展招商办公场景的自动化提效。所有敏感数据处理均在本地完成，兼顾了智能性、隐私性和成本。

---

**项目地址**：[https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant](https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant)
**提交包**：[Release v1.0.0](https://github.com/yigenfeng0707-netizen/meetgrow-office-assistant/releases/tag/v1.0.0)
**标签**：`Intel AI PC`、`Agent Skills`、`OCR`、`ASR`、`TTS`
