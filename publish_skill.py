#!/usr/bin/env python3
"""
MeetGrow AI PC Agent Skill - 魔搭社区提交脚本

功能:
1. 验证项目完整性 (检查所有必需文件)
2. 生成 Skill JSON 定义文件
3. 创建提交包 (ZIP 压缩)
4. 计算文件哈希值 (用于完整性校验)

用法:
    python publish_skill.py              # 默认提交到 D:\meetgrow-agent-skill
    python publish_skill.py --output dist  # 输出到 dist/ 目录
    python publish_skill.py --verbose      # 详细输出
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("publish_skill")


class SkillPublisher:
    """魔搭社区 Skill 提交器"""

    # 必需的目录
    REQUIRED_DIRS = [
        "meetgrow_skill",
        "meetgrow_skill/core",
        "meetgrow_skill/tools",
        "examples",
        "tests",
    ]

    # 必需的文件
    REQUIRED_FILES = [
        "README.md",
        "README_zh.md",
        "requirements.txt",
        "environment.yml",
        "pyproject.toml",
        "meetgrow_skill/__init__.py",
        "meetgrow_skill/__main__.py",
        "meetgrow_skill/config.py",
        "meetgrow_skill/skill.py",
        "meetgrow_skill/core/__init__.py",
        "meetgrow_skill/core/agent.py",
        "meetgrow_skill/core/orchestrator.py",
        "meetgrow_skill/core/memory.py",
        "meetgrow_skill/tools/__init__.py",
        "meetgrow_skill/tools/base.py",
        "meetgrow_skill/tools/ocr_tool.py",
        "meetgrow_skill/tools/asr_tool.py",
        "meetgrow_skill/tools/tts_tool.py",
        "meetgrow_skill/tools/doc_tool.py",
        "examples/demo_card_ocr.py",
        "examples/demo_meeting_minutes.py",
        "examples/demo_complete_agent.py",
        "tests/__init__.py",
        "tests/test_ocr.py",
        "tests/test_asr.py",
        "tests/test_orchestrator.py",
    ]

    # 可选文件
    OPTIONAL_FILES = [
        "docs/tech_article.md",
        "meetgrow_skill/core/memory.py",
        "examples/demo_voice_assistant.py",
        "tests/test_orchestrator.py",
    ]

    def __init__(self, project_dir: str, output_dir: str = None, verbose: bool = False):
        self.project_dir = Path(project_dir).resolve()
        self.output_dir = Path(output_dir).resolve() if output_dir else self.project_dir / "dist"
        self.verbose = verbose
        self.checks = []
        self.warnings = []

    def log(self, msg: str, level: str = "info"):
        if self.verbose or level == "error" or level == "warning":
            func = getattr(logger, level)
            func(msg)
        elif level == "info":
            logger.info(msg)

    # ---- 完整性检查 ----

    def check_directories(self) -> bool:
        """检查必需目录是否存在"""
        self.log("📂 检查目录结构...")
        all_ok = True
        for d in self.REQUIRED_DIRS:
            path = self.project_dir / d
            if path.is_dir():
                self.log(f"  ✅ {d}/")
            else:
                self.log(f"  ❌ 缺少目录: {d}/", "error")
                all_ok = False
                self.warnings.append(f"Missing directory: {d}/")
        self.checks.append({"check": "directories", "passed": all_ok})
        return all_ok

    def check_files(self) -> bool:
        """检查必需文件是否存在"""
        self.log("📄 检查必需文件...")
        all_ok = True
        for f in self.REQUIRED_FILES:
            path = self.project_dir / f
            if path.is_file():
                self.log(f"  ✅ {f}")
            else:
                self.log(f"  ❌ 缺少文件: {f}", "error")
                all_ok = False
                self.warnings.append(f"Missing file: {f}")
        self.checks.append({"check": "files", "passed": all_ok})
        return all_ok

    def check_optional(self) -> list[str]:
        """检查可选文件（不阻塞提交）"""
        self.log("📦 检查可选文件...")
        found = []
        for f in self.OPTIONAL_FILES:
            path = self.project_dir / f
            if path.is_file():
                found.append(f)
                self.log(f"  ✅ {f}")
            else:
                self.log(f"  ℹ️  可选文件缺失: {f}")
        return found

    def check_requirements(self) -> bool:
        """检查 requirements.txt 格式"""
        self.log("📋 检查 requirements.txt...")
        req_file = self.project_dir / "requirements.txt"
        if not req_file.exists():
            self.log("  ❌ requirements.txt 不存在", "error")
            self.checks.append({"check": "requirements", "passed": False})
            return False

        try:
            content = req_file.read_text(encoding="utf-8")
            packages = [
                line.strip() for line in content.split("\n")
                if line.strip() and not line.startswith("#") and not line.startswith("-")
            ]
            self.log(f"  ✅ 找到 {len(packages)} 个依赖包")
            self.checks.append({"check": "requirements", "passed": True})
            return True
        except Exception as e:
            self.log(f"  ❌ requirements.txt 解析失败: {e}", "error")
            self.checks.append({"check": "requirements", "passed": False})
            return False

    # ---- Skill 定义生成 ----

    def generate_skill_json(self) -> dict:
        """生成魔搭社区 Skill JSON 定义"""
        self.log("🔧 生成 Skill 定义...")

        # 动态导入 SkillDefinition
        project_str = str(self.project_dir)
        if project_str not in sys.path:
            sys.path.insert(0, project_str)

        try:
            from meetgrow_skill.skill import SkillDefinition
            skill = SkillDefinition()
        except ImportError as e:
            self.log(f"  ❌ 无法导入 SkillDefinition: {e}", "error")
            return {}

        skill_data = {
            "metadata": {
                "name": skill.metadata.name,
                "version": skill.metadata.version,
                "title": skill.metadata.title,
                "description": skill.metadata.description,
                "author": skill.metadata.author,
                "license": skill.metadata.license,
                "tags": skill.metadata.tags,
                "created_at": datetime.now().isoformat(),
            },
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                    "examples": t.examples,
                }
                for t in skill.tools
            ],
            "architecture": {
                "brain": "Qwen3.6-35B-A3B (API)",
                "local_tools": ["PaddleOCR", "FunASR", "edge-tts", "DocEng"],
                "hardware": "Intel Core Ultra 5 125H (CPU + Arc GPU + NPU)",
            },
            "scenarios": [
                {"name": "名片 OCR 识别", "tools": ["ocr_business_card"]},
                {"name": "会议纪要生成", "tools": ["speech_to_text", "generate_meeting_minutes"]},
                {"name": "智能语音播报", "tools": ["text_to_speech"]},
                {"name": "资料归档", "tools": ["smart_archive"]},
            ],
        }

        # 保存到 dist 目录
        skill_file = self.output_dir / "meetgrow_skill.json"
        skill_file.write_text(
            json.dumps(skill_data, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8"
        )
        self.log(f"  ✅ Skill JSON: {skill_file}")
        return skill_data

    # ---- 打包提交 ----

    def calculate_hash(self, filepath: Path) -> str:
        """计算文件 MD5 哈希"""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]

    def generate_manifest(self, skill_data: dict) -> dict:
        """生成提交清单"""
        self.log("📋 生成提交清单...")
        manifest = {
            "project": skill_data.get("metadata", {}).get("name", "meetgrow-office-assistant"),
            "version": skill_data.get("metadata", {}).get("version", "1.0.0"),
            "generated_at": datetime.now().isoformat(),
            "files": {},
            "checks": self.checks,
            "warnings": self.warnings,
        }

        for f in self.REQUIRED_FILES:
            path = self.project_dir / f
            if path.exists():
                manifest["files"][f] = {
                    "size": path.stat().st_size,
                    "hash": self.calculate_hash(path),
                }

        # 统计信息
        total_size = sum(
            f["size"] for f in manifest["files"].values()
        )
        manifest["statistics"] = {
            "total_files": len(manifest["files"]),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "tool_count": len(skill_data.get("tools", [])),
            "scenario_count": len(skill_data.get("scenarios", [])),
        }

        # 保存到 dist
        manifest_file = self.output_dir / "manifest.json"
        manifest_file.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        self.log(f"  ✅ 清单: {manifest_file}")
        return manifest

    def create_zip_package(self) -> str:
        """创建 ZIP 提交包 - 只打包源代码文件"""
        self.log("📦 创建 ZIP 提交包...")

        import zipfile
        
        # 只打包这些必需目录和文件
        files_to_pack = [
            "README.md", "README_zh.md", "requirements.txt", 
            "environment.yml", "pyproject.toml",
            "meetgrow_skill/__init__.py", "meetgrow_skill/__main__.py",
            "meetgrow_skill/config.py", "meetgrow_skill/skill.py",
            "meetgrow_skill/core/__init__.py", "meetgrow_skill/core/agent.py",
            "meetgrow_skill/core/orchestrator.py", "meetgrow_skill/core/memory.py",
            "meetgrow_skill/tools/__init__.py", "meetgrow_skill/tools/base.py",
            "meetgrow_skill/tools/ocr_tool.py", "meetgrow_skill/tools/asr_tool.py",
            "meetgrow_skill/tools/tts_tool.py", "meetgrow_skill/tools/doc_tool.py",
            "examples/demo_card_ocr.py", "examples/demo_meeting_minutes.py",
            "examples/demo_complete_agent.py",
            "tests/__init__.py", "tests/test_ocr.py", "tests/test_asr.py",
            "tests/test_orchestrator.py",
            "docs/tech_article.md",
        ]
        
        clean_zip = self.output_dir / f"meetgrow-skill-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
        
        # 检查所有文件是否存在
        missing = [f for f in files_to_pack if not (self.project_dir / f).exists()]
        if missing:
            self.log(f"  ⚠️  以下文件不存在，跳过：", "warning")
            for m in missing:
                self.log(f"     - {m}", "warning")
            # 过滤掉不存在的文件
            files_to_pack = [f for f in files_to_pack if (self.project_dir / f).exists()]

        with zipfile.ZipFile(clean_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for arc_name in files_to_pack:
                file_path = self.project_dir / arc_name
                if file_path.exists():
                    zf.write(file_path, arc_name)
                    self.log(f"    ✓ {arc_name}")

        self.log(f"  ✅ ZIP 包: {clean_zip}")
        self.log(f"     大小: {clean_zip.stat().st_size / 1024 / 1024:.1f} MB")
        return str(clean_zip)

    # ---- 主流程 ----

    def run(self) -> bool:
        """执行完整提交流程"""
        self.log("=" * 60)
        self.log(f"MeetGrow AI PC Agent Skill - 魔搭社区提交")
        self.log(f"项目目录: {self.project_dir}")
        self.log(f"输出目录: {self.output_dir}")
        self.log("=" * 60)

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: 完整性检查
        self.log("\n📊 第一步: 完整性检查")
        dirs_ok = self.check_directories()
        files_ok = self.check_files()
        req_ok = self.check_requirements()
        optional = self.check_optional()

        # 汇总检查
        all_passed = dirs_ok and files_ok and req_ok
        self.log(f"\n{'=' * 60}")
        if all_passed:
            self.log("✅ 所有检查通过！可以提交。")
        else:
            self.log("❌ 检查未通过，请修复以下问题后重新提交：", "warning")
            for w in self.warnings:
                self.log(f"   - {w}", "warning")
            return False

        # Step 2: 生成 Skill JSON
        self.log("\n📊 第二步: 生成 Skill 定义")
        skill_data = self.generate_skill_json()
        if not skill_data:
            self.log("❌ Skill 定义生成失败", "error")
            return False

        # Step 3: 生成提交清单
        self.log("\n📊 第三步: 生成提交清单")
        manifest = self.generate_manifest(skill_data)
        self.log(f"   文件数: {manifest['statistics']['total_files']}")
        self.log(f"   总大小: {manifest['statistics']['total_size_mb']} MB")
        self.log(f"   工具数: {manifest['statistics']['tool_count']}")

        # Step 4: 创建 ZIP 包
        self.log("\n📊 第四步: 创建 ZIP 提交包")
        zip_path = self.create_zip_package()

        # 最终报告
        self.log(f"\n{'=' * 60}")
        self.log("🎉 提交包准备完成！")
        self.log(f"   Skill JSON: {self.output_dir / 'meetgrow_skill.json'}")
        self.log(f"   提交清单:   {self.output_dir / 'manifest.json'}")
        self.log(f"   ZIP 包:     {zip_path}")
        self.log(f"\n下一步: 登录魔搭社区，上传 ZIP 包和 Skill JSON")
        self.log(f"        网址: https://modelscope.cn/my/myskill")
        self.log(f"{'=' * 60}")

        return True


def main():
    parser = argparse.ArgumentParser(
        description="MeetGrow AI PC Agent Skill - 魔搭社区提交工具"
    )
    parser.add_argument(
        "--project", "-p",
        type=str,
        default=str(Path(__file__).parent.resolve()),
        help="项目根目录路径 (默认: 脚本所在目录)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出目录 (默认: 项目目录/dist)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )

    args = parser.parse_args()
    publisher = SkillPublisher(args.project, args.output, args.verbose)
    success = publisher.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
