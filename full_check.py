"""
MeetGrow 项目总检查 + 自动修复脚本
一次性完成：目录检查、文件完整性、测试、publish_skill.py
"""
import os, sys, json, time, subprocess, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

def run(cmd, timeout=300):
    """安全执行命令"""
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout, shell=isinstance(cmd, str))
        return r.stdout + r.stderr, r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 1

def main():
    print("=" * 60)
    print("🔍 MeetGrow 项目总检查 — " + time.strftime("%Y-%m-%d %H:%M"))
    print("=" * 60)
    
    t0 = time.time()
    
    # ==================== 1. 目录结构检查 ====================
    print("\n📁 目录结构:")
    dirs = {
        "meetgrow_skill/core": False,
        "meetgrow_skill/tools": False,
        "examples": False,
        "tests": False,
        "docs": False,
    }
    for d in dirs:
        p = ROOT / d
        if p.is_dir():
            files = list(p.rglob("*.py"))
            dirs[d] = True
            print(f"  ✅ {d}/ ({len(files)} py files)")
        else:
            print(f"  ❌ {d}/ MISSING")
    
    # ==================== 2. 关键文件检查 ====================
    print("\n📄 关键文件:")
    req = [
        "README.md", "README_zh.md", "publish_skill.py",
        "meetgrow_skill/__init__.py", "meetgrow_skill/skill.py",
        "meetgrow_skill/__main__.py", "meetgrow_skill/config.py",
        "meetgrow_skill/core/agent.py", "meetgrow_skill/core/orchestrator.py",
        "meetgrow_skill/core/memory.py",
        "meetgrow_skill/tools/base.py",
        "meetgrow_skill/tools/ocr_tool.py", "meetgrow_skill/tools/asr_tool.py",
        "meetgrow_skill/tools/tts_tool.py", "meetgrow_skill/tools/doc_tool.py",
        "examples/demo_card_ocr.py", "examples/demo_meeting_minutes.py",
        "docs/tech_article.md",
    ]
    missing = []
    for f in req:
        p = ROOT / f
        if p.exists():
            size = p.stat().st_size
            print(f"  ✅ {f} ({size}B)")
        else:
            missing.append(f)
            print(f"  ❌ {f} MISSING")
    
    if missing:
        print(f"\n⚠️  缺少 {len(missing)} 个文件:")
        for m in missing:
            print(f"    - {m}")
    else:
        print("\n✅ 所有必需文件存在")
    
    # ==================== 3. 统计 ====================
    py_files = list(ROOT.rglob("*.py"))
    test_files = [f for f in py_files if f.name.startswith("test_")]
    total_lines = 0
    for f in py_files:
        try:
            total_lines += sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))
        except: pass
    
    print(f"\n📊 代码统计:")
    print(f"  Python 文件: {len(py_files)}")
    print(f"  测试文件: {len(test_files)}")
    print(f"  总行数: {total_lines}")
    
    # ==================== 4. 技术文章 ====================
    article = ROOT / "docs" / "tech_article.md"
    if article.exists():
        content = article.read_text(encoding="utf-8")
        chinese = sum(1 for c in content if '\u4e00' <= c <= '\u9fff')
        print(f"\n📝 技术文章: {len(content)} 字符, ~{chinese} 中文字")
    else:
        print(f"\n❌ 技术文章缺失!")
    
    # ==================== 5. JSON/ZIP 产出文件 ====================
    print(f"\n📦 产出文件:")
    for f in ROOT.glob("*.json"):
        print(f"  {f.name} ({f.stat().st_size}B)")
    for f in ROOT.glob("*.zip"):
        print(f"  {f.name} ({f.stat().st_size}B)")
    
    # ==================== 6. publish_skill.py 预检 ====================
    print(f"\n🔧 publish_skill.py 预检:")
    ps_path = ROOT / "publish_skill.py"
    if ps_path.exists():
        code = ps_path.read_text(encoding="utf-8")
        # 检查是否有 validate 或 check 相关逻辑
        if "validate" in code.lower() or "check" in code.lower():
            print("  包含验证逻辑")
        # 检查依赖的文件引用
        refs = re.findall(r'(?:file|path)[\s\"\'=]*[\'\"](.*?)[\'\"]', code, re.I)
        deps = []
        for r in refs:
            p = ROOT / r
            if not p.exists():
                deps.append(r)
        if deps:
            print(f"  ❌ 缺少依赖: {deps}")
        else:
            print("  ✅ 依赖完整")
    else:
        print("  ❌ publish_skill.py 不存在!")
    
    # ==================== 7. 运行 pytest ====================
    print(f"\n🧪 pytest (等待...)")
    sys.stdout.flush()
    
    output, code = run([PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short", "-q"], timeout=120)
    print(output[-2000:])
    
    if "error" in output.lower() or code != 0:
        print(f"\n⚠️  测试未全部通过")
    else:
        print(f"\n✅ 测试全部通过")
    
    # ==================== 8. 完整总结 ====================
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print(f"✅ 总检查完成 — {elapsed:.1f}s")
    print("=" * 60)
    
    return 0 if code == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
