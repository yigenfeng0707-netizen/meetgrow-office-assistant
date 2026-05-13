"""
MeetGrow AI PC Agent Skill - 演示脚本
名片 OCR 识别演示

用法:
    cd D:\meetgrow-agent-skill
    python examples/demo_card_ocr.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from meetgrow_skill.config import get_config
from meetgrow_skill.tools.ocr_tool import OCRTool


def main():
    print("=" * 60)
    print("📄 MeetGrow AI - 名片 OCR 识别演示")
    print("=" * 60)

    # 获取配置
    config = get_config()
    print(f"\n📁 工作目录: {config.workspace_dir}")

    # 创建 OCR 工具（名片识别模式）
    ocr = OCRTool(config, task="business_card")

    # 查找测试图片
    demo_dir = Path(__file__).parent
    test_images = [
        demo_dir / "test_card.jpg",
        demo_dir / "test_card.png",
    ]

    # 如果没有测试图片，使用演示模式
    test_image = None
    for img in test_images:
        if img.exists():
            test_image = str(img)
            break

    if test_image is None:
        print("\n⚠️  未找到测试图片")
        print("\n演示模式: 展示 OCR 工具能力和使用方式\n")
        print("📋 名片 OCR 识别功能:")
        print("   • 识别姓名、公司、职位")
        print("   • 识别电话、邮箱")
        print("   • 支持中英文名片")
        print("   • 输出结构化 JSON 数据")
        print()
        print("使用方法:")
        print("   meetgrow ocr path/to/card.jpg")
        print("   # 或 Python API:")
        print("   ocr = OCRTool(config, task='business_card')")
        print("   result = ocr.execute(image_path='card.jpg')")
        print()
        print("示例输出:")
        print('   {')
        print('     "name": "张三",')
        print('     "company": "XX科技有限公司",')
        print('     "title": "采购总监",')
        print('     "phone": "138-0000-0000",')
        print('     "email": "zhangsan@example.com"')
        print('   }')
        return

    print(f"\n🔍 识别图片: {test_image}")

    # 执行 OCR
    result = ocr.execute(image_path=test_image)

    if result.get("status") == "success":
        print(f"\n✅ 识别成功!")
        print(f"\n📄 识别文本:")
        print(result.get("text", "无内容"))

        processed = result.get("processed", {})
        if processed:
            print(f"\n📋 解析的结构化信息:")
            import json
            print(json.dumps(processed, ensure_ascii=False, indent=2))
    else:
        print(f"\n❌ 识别失败: {result.get('error', '未知错误')}")
        print("\n💡 请确保已安装: pip install paddlepaddle paddleocr")


if __name__ == "__main__":
    main()
