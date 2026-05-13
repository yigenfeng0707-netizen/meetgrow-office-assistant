"""完整测试 - 全部跑完看失败"""
import subprocess, sys, os
os.chdir(r"D:\meetgrow-agent-skill")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-q", "--no-header", "--disable-warnings"],
    capture_output=True, text=True, encoding="utf-8"
)
# 只输出失败部分
lines = result.stdout.split("\n")
found_failures = False
for i, line in enumerate(lines):
    if "FAILED" in line or "failures" in line.lower() or "error" in line.lower() or "=== " in line:
        print(line)
        found_failures = True
    elif found_failures and "===" in line:
        print(line)
        found_failures = False
    elif "FAILED" in line or "assert" in line.lower() or "E " in line:
        print(line)
        found_failures = True
    elif found_failures:
        print(line)

# 最后打印总结
print("\n\n=== 全部行 ===")
# 只打印 FAILED 行和总结
for line in lines:
    if "FAILED" in line or "short test summary" in line or "===" in line:
        print(line)
print(f"\nEXIT CODE: {result.returncode}")
