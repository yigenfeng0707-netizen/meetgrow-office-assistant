"""快速测试 - 只看失败"""
import subprocess, sys, os
os.chdir(r"D:\meetgrow-agent-skill")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-x", "-v", "--tb=long", "-q"],
    capture_output=True, text=True, encoding="utf-8"
)
print("=== STDOUT ===")
print(result.stdout)
if result.stderr:
    print("=== STDERR ===")
    print(result.stderr)
print(f"\n=== EXIT CODE: {result.returncode} ===")
