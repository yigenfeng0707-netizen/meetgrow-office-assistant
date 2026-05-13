import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "--tb=short", "-q", "--no-header"],
    capture_output=True,
    text=True,
    cwd=r"D:\meetgrow-agent-skill",
    timeout=180
)

# Write output to file
with open("D:\\meetgrow-agent-skill\\test_results.txt", "w", encoding="utf-8") as f:
    f.write(f"Return code: {result.returncode}\n")
    f.write("STDOUT:\n")
    f.write(result.stdout)
    f.write("\nSTDERR:\n")
    f.write(result.stderr)

print(f"Done: {result.returncode}")
