"""
MeetGrow AI PC Agent Skill - 演示脚本
会议录音 → 会议纪要生成演示

用法:
    cd D:\meetgrow-agent-skill
    python examples/demo_meeting_minutes.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.asr_tool import ASRTool
from meetgrow_skill.tools.doc_tool import DocTool


def main():
    print("=" * 60)
    print("📝 MeetGrow AI - 会议录音转纪要演示")
    print("=" * 60)

    config = get_config()

    # 演示流程说明
    print("\n📋 会议转纪要流程:")
    print("   1️⃣  录音文件 → ASR 转写 → 文字稿")
    print("   2️⃣  文字稿 → Agent 整理 → 会议纪要")
    print("   3️⃣  会议纪要 → 结构化输出 (Markdown)")
    print()

    # 模拟会议转写文本
    sample_transcript = """
主持人: 好的，我们开始今天的 Q2 招商推进会。
先请各区域负责人汇报一下进展。

华东区-李经理: 华东区目前签约了15家企业，完成率60%。主要客户集中在杭州和苏州。

华南区-王总监: 华南区签约22家，完成率85%。深圳会展中心的展位已全部售出。

华北区-张经理: 华北区签约10家，完成率40%，进度稍慢。需要加大力度。

主持人: 好的，华南区表现不错。华东区下个月需要加快速度。
另外，今年的展位价格有5%的上调，大家做好客户沟通。

华东区-李经理: 明白，我今天就通知客户。

主持人: 还有一个问题，今年的论坛嘉宾需要尽快确认，
市场部本周内把嘉宾名单整理出来。

各区域-众人: 好的。
    """

    print("📝 示例会议转写文本:")
    print("-" * 40)
    print(sample_transcript.strip())
    print("-" * 40)

    # 创建文档处理工具
    doc_tool = DocTool(config, task="minutes")

    print("\n🔄 正在调用 Agent API 生成会议纪要...")
    print("   (需要配置 API Key 才能实际执行)")
    print()

    # 生成会议纪要的提示词预览
    from datetime import datetime
    prompt_preview = f"""会议纪要生成预览:

会议标题: Q2 招商推进会
会议日期: {datetime.now().strftime('%Y-%m-%d')}

### 议程
1. 各区域招商进展汇报
2. 展位价格调整通知
3. 论坛嘉宾确认

### 会议摘要
本次 Q2 招商推进会总结了各区域招商进展。华南区表现最优(85%)，
华东区(60%)和华北区(40%)需加强推进力度。

### 决策事项
- [x] 展位价格上调 5%
- [ ] 各区域加快签约进度
- [ ] 市场部整理论坛嘉宾名单

### 待办事项
| 负责人 | 任务 | 截止日期 |
|--------|------|----------|
| 李经理(华东) | 通知客户展位价格调整 | 当日 |
| 市场部 | 整理论坛嘉宾名单 | 本周内 |
| 张经理(华北) | 加快华北区招商进度 | 下月 |
"""

    print("📄 预期会议纪要结构:")
    print("-" * 40)
    print(prompt_preview.strip())
    print("-" * 40)

    # 实际执行（如果 API 可用）
    print("\n💡 如需实际生成，请:")
    print("   1. 设置 API Key: export MODELSCOPE_API_KEY=your_key")
    print("   2. 运行: meetgrow agent '将以下转写文本生成纪要'" )
    print()
    print("   ASR 工具用法:")
    print("   meetgrow asr path/to/meeting.wav")
    print()
    print("   集成流程:")
    print("   meetgrow asr meeting.wav  # 转写")
    print("   meetgrow agent '整理会议纪要'  # Agent 整理")


if __name__ == "__main__":
    main()
