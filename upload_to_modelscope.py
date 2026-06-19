#!/usr/bin/env python3
"""
MeetGrow AI PC Agent Skill - 魔搭社区自动上传脚本
使用 ModelScope API 自动上传 ZIP 包
"""

import os
import sys
import json
import requests

# 配置（请通过环境变量 MODELSCOPE_API_TOKEN 传入，避免硬编码）
API_TOKEN = os.environ.get("MODELSCOPE_API_TOKEN", "")
PROJECT_DIR = r"D:\meetgrow-agent-skill"
DIST_DIR = os.path.join(PROJECT_DIR, "dist")

# 自动匹配最新的提交包
zip_files = sorted(Path(DIST_DIR).glob("meetgrow-skill-*.zip"))
ZIP_FILE = str(zip_files[-1]) if zip_files else os.path.join(DIST_DIR, "meetgrow-skill.zip")
SKILL_JSON = os.path.join(DIST_DIR, "meetgrow_skill.json")

# ModelScope API 端点（根据魔搭社区文档）
UPLOAD_ENDPOINT = "https://modelscope.cn/api/v1/skills/upload"  # 需要确认
UPLOAD_ENDPOINT = "https://modelscope.cn/api/upload"
UPLOAD_ENDPOINT = "https://api.modelscope.cn/api/upload"

def upload_file(file_path, file_name, token):
    """上传文件到魔搭社区"""
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    file_size = os.path.getsize(file_path)
    print(f"📁 上传文件：{file_name} ({file_size / 1024:.1f} KB)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Api-Key": token
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f)}
            response = requests.post(
                UPLOAD_ENDPOINT,
                headers=headers,
                files=files,
                timeout=30
            )
            
        if response.status_code in [200, 201]:
            print(f"✅ 上传成功！响应：{response.text[:200]}")
            return True
        else:
            print(f"❌ 上传失败：{response.status_code}")
            print(f"   响应：{response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ 上传异常：{e}")
        return False

def main():
    print("=" * 60)
    print("MeetGrow AI PC Agent Skill - 魔搭社区自动上传")
    print("=" * 60)
    
    # 检查文件
    print("\n📋 检查上传文件...")
    if not os.path.exists(ZIP_FILE):
        print(f"❌ ZIP 包不存在：{ZIP_FILE}")
        sys.exit(1)
    if not os.path.exists(SKILL_JSON):
        print(f"❌ Skill JSON 不存在：{SKILL_JSON}")
        sys.exit(1)
    
    # 上传 ZIP 包
    print("\n📦 上传 ZIP 包...")
    zip_success = upload_file(ZIP_FILE, "meetgrow-skill.zip", API_TOKEN)
    
    # 上传 Skill JSON
    print("\n📄 上传 Skill JSON...")
    json_success = upload_file(SKILL_JSON, "meetgrow_skill.json", API_TOKEN)
    
    if zip_success and json_success:
        print("\n🎉 上传完成！")
    else:
        print("\n⚠️ 部分上传失败，请检查")
        sys.exit(1)

if __name__ == "__main__":
    main()
