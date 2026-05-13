# MeetGrow AI PC Agent Skill

> 英特尔 × 魔搭社区：AI PC Agent Skills 征文活动参赛作品

## 📋 项目概述

MeetGrow AI PC Agent Skill 是一个运行在 **Intel AI PC** 上的本地化智能办公助手。它利用 **≤35B 参数的小模型** 作为 Agent 大脑，调度本地工具（OCR / ASR / TTS），实现会展招商办公提效场景的自动化。

## 🎯 核心主题

> 用 35B 以下小模型作为 Agent 大脑，驱动一项本地 AI 工具调用（OCR、ASR、TTS…），满足实际场景需求，最终生成可被复用的 Agent Skill。

## 📊 评分要点覆盖

| 评分项 | 权重 | 本项目满足情况 |
|--------|------|---------------|
| 技术合理性 | 30% | ✅ 35B-A3B + PaddleOCR + FunASR + edge-tts，技术栈成熟稳定 |
| 场景实用性 | 30% | ✅ 会展招商场景全覆盖：名片识别、会议纪要、资料归档 |
| 创新性 | 20% | ✅ Agent 编排 + 多工具链式调度 + MeetGrow 行业场景深度融合 |
| 完整性 | 10% | ✅ 完整项目代码 + 文档 + 示例 + 测试 + 征文文章 |
| 推广价值 | 10% | ✅ 模块化设计，可复制到其他办公场景 |

## 🏗️ 架构

```
┌──────────────────────────────────────────────────┐
│              MeetGrow AI PC Agent                  │
├──────────────────────────────────────────────────┤
│  Agent Brain (Qwen3.6-35B-A3B via API)           │
│  ├── Intent Router: 意图识别 → 工具选择           │
│  ├── Tool Planner: 编排工具调用链                 │
│  └── Memory Manager: 上下文管理                   │
├──────────────────────────────────────────────────┤
│  Local Tools (纯本地运行，支持 OpenVINO)           │
│  ├── OCR: PaddleOCR (PP-OCRv5)                   │
│  ├── ASR: FunASR (Paraformer)                    │
│  ├── TTS: edge-tts (微软免费)                    │
│  └── DocEng: 文档解析引擎                         │
├──────────────────────────────────────────────────┤
│  MeetGrow AI 集成                                  │
│  ├── 🎫 名片 OCR → 自动建档案                     │
│  ├── 📝 会议录音 → 自动生成纪要                   │
│  ├── 📊 资料扫描 → 结构化归档                     │
│  └── 📢 TTS → 语音播报待办                        │
└──────────────────────────────────────────────────┘
```

## ⚙️ 技术约束满足

- **模型规格**: Qwen3.6-35B-A3B，总参数量 ≤ 35B ✅
- **运行环境**: 纯本地工具，API 调用模型，零云端依赖 ✅
- **推理框架**: 支持 OpenVINO (PaddleOCR / FunASR 均可导出) ✅
- **硬件平台**: Intel Core Ultra 5 125H (CPU + Arc GPU + NPU) ✅

## 🚀 快速开始

```bash
# 1. 创建 conda 环境
conda create -n meetgrow python=3.11 -y
conda activate meetgrow

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化（自动下载模型权重）
python -m meetgrow_skill init

# 4. 运行示例
python examples/demo_card_ocr.py
python examples/demo_meeting_minutes.py
python examples/demo_complete_agent.py
```

## 📁 项目结构

```
meetgrow-agent-skill/
├── README.md                          # 项目说明
├── README_zh.md                       # 中文详细说明
├── requirements.txt                   # Python 依赖
├── environment.yml                    # Conda 环境配置
├── pyproject.toml                     # 项目元数据
│
├── meetgrow_skill/                    # 核心包
│   ├── __init__.py
│   ├── __main__.py                    # CLI 入口
│   ├── config.py                      # 配置管理
│   ├── skill.py                       # Skill 定义
│   │
│   ├── core/                          # 核心模块
│   │   ├── __init__.py
│   │   ├── agent.py                   # Agent 大脑（意图路由 + 工具编排）
│   │   ├── memory.py                  # 记忆 / 上下文管理
│   │   └── orchestrator.py            # 多工具链式调度器
│   │
│   └── tools/                         # 本地工具
│       ├── __init__.py
│       ├── base.py                    # 工具基类
│       ├── ocr_tool.py                # OCR 工具 (PaddleOCR)
│       ├── asr_tool.py                # 语音识别 (FunASR)
│       ├── tts_tool.py                # 语音合成 (edge-tts)
│       └── doc_tool.py                # 文档处理工具
│
├── examples/                          # 示例代码
│   ├── demo_card_ocr.py              # 名片 OCR 识别
│   ├── demo_meeting_minutes.py       # 会议纪要生成
│   ├── demo_complete_agent.py        # 完整 Agent 演示
│   └── demo_voice_assistant.py       # 语音助手演示
│
├── tests/                             # 测试
│   ├── __init__.py
│   ├── test_ocr.py
│   ├── test_asr.py
│   └── test_orchestrator.py
│
└── models/                            # 模型权重目录
```

## 📊 MeetGrow AI 场景映射

MeetGrow AI 12 模块中的多个模块直接复用本 Agent Skill 的本地工具：

| MeetGrow 模块 | 使用的本地工具 | 功能 |
|--------------|---------------|------|
| 活动名片采集 | PaddleOCR | 参会者名片扫描识别 |
| 活动纪要 | FunASR + Agent | 会议录音转写 + 智能摘要 |
| 活动照片管理 | PaddleOCR | 照片文字信息提取 |
| 智能客服 | Agent Brain | 用户意图理解 + 自动回复 |
| 活动签到 | PaddleOCR | 证件/名片快速识别签到 |
| 智能邀约 | Agent Brain | 基于名片信息的个性化邀约 |

## 🏆 预期成果

1. **可运行的 Agent Skill** - 完整的本地 AI 办公助手
2. **3 个典型场景演示** - 名片识别、会议纪要、语音助手
3. **征文技术文章** - 完整的技术架构和实现细节
4. **Demo 视频** - 录制演示视频作为投稿附件

---

*Powered by Intel AI PC + ModelScope + MeetGrow AI*
