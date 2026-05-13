"""全部跑完 - 不stop"""
import subprocess, sys, os
os.chdir(r"D:\meetgrow-agent-skill")
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=line", "-q", "--no-header", "--disable-warnings"],
    capture_output=True, text=True, encoding="utf-8"
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
print(f"\n=== EXIT: {result.returncode} ===")
