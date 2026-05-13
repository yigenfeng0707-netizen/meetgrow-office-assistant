# Quick Status Check - PowerShell
$ErrorActionPreference = 'SilentlyContinue'
$ROOT = "D:\meetgrow-agent-skill"
$python = "C:\Users\52637\miniconda3\envs\meetgrow\python.exe"

Write-Host "=== MEETGROW 项目状态总览 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 目录结构
Write-Host "[1/5] 目录结构检查..." -ForegroundColor Yellow
$requiredDirs = @("meetgrow_skill/core", "meetgrow_skill/tools", "examples", "tests", "docs")
foreach ($d in $requiredDirs) {
    $path = Join-Path $ROOT $d
    if (Test-Path $path) {
        $files = (Get-ChildItem $path -File -Recurse).Count
        Write-Host "  ✅ $d/ ($files files)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $d/ MISSING" -ForegroundColor Red
    }
}

# 2. 关键文件
Write-Host "[2/5] 关键文件..." -ForegroundColor Yellow
$reqFiles = @(
    "README.md", "README_zh.md", "publish_skill.py",
    "meetgrow_skill/__init__.py", "meetgrow_skill/skill.py",
    "meetgrow_skill/__main__.py", "meetgrow_skill/config.py",
    "meetgrow_skill/core/agent.py", "meetgrow_skill/core/orchestrator.py",
    "meetgrow_skill/core/memory.py",
    "meetgrow_skill/tools/base.py", "meetgrow_skill/tools/ocr_tool.py",
    "meetgrow_skill/tools/asr_tool.py", "meetgrow_skill/tools/tts_tool.py",
    "meetgrow_skill/tools/doc_tool.py",
    "examples/demo_card_ocr.py", "examples/demo_meeting_minutes.py",
    "docs/tech_article.md"
)
foreach ($f in $reqFiles) {
    $path = Join-Path $ROOT $f
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "  ✅ $f ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $f MISSING" -ForegroundColor Red
    }
}

# 3. 统计
Write-Host "[3/5] 代码统计..." -ForegroundColor Yellow
$pyFiles = Get-ChildItem $ROOT -Recurse -Filter "*.py" -File
$testFiles = Get-ChildItem $ROOT -Filter "test_*.py" -File
$totalLines = 0
foreach ($f in $pyFiles) {
    $totalLines += (Get-Content $f -ErrorAction SilentlyContinue).Count
}
Write-Host "  Python files: $($pyFiles.Count)"
Write-Host "  Test files: $($testFiles.Count)"
Write-Host "  Total lines: $totalLines"

# 4. 技术文章字数
Write-Host "[4/5] 技术文章..." -ForegroundColor Yellow
$article = Join-Path $ROOT "docs/tech_article.md"
if (Test-Path $article) {
    $content = Get-Content $article -Raw -Encoding UTF8
    Write-Host "  字符数: $($content.Length)" -ForegroundColor Green
    $chinese = ($content | Select-String -Pattern '[\u4e00-\u9fff]' -AllMatches).Matches.Count
    Write-Host "  中文字数: ~$chinese" -ForegroundColor Green
}

# 5. JSON 配置
Write-Host "[5/5] 配置/产出文件..." -ForegroundColor Yellow
$jsonFiles = Get-ChildItem $ROOT -Filter "*.json" -File
foreach ($f in $jsonFiles) {
    Write-Host "  $($f.Name) ($($f.Length) bytes)"
}

# 6. publish_skill.py 状态
Write-Host "" -ForegroundColor White
Write-Host "=== publish_skill.py 检查 ===" -ForegroundColor Cyan

# 快速运行 pytest (只跑测试，不跑 publish)
Write-Host "运行 pytest..." -ForegroundColor Yellow
$ts = Get-Date
try {
    $result = Start-Process $python -ArgumentList "-m", "pytest", "tests/", "-v", "--tb=short", "-q", "-W", "ignore" `
        -WorkingDirectory $ROOT -NoNewWindow -PassThru -Wait -RedirectStandardOutput "$ROOT\test_out.txt" -RedirectStandardError "$ROOT\test_err.txt"
    # 等 90 秒后检查
    $elapsed = 0
    while ($elapsed -lt 90 -and $result.HasExited -eq $false) {
        Start-Sleep -Seconds 5
        $elapsed += 5
    }
    if ($result.HasExited) {
        Write-Host "测试完成" -ForegroundColor Green
    } else {
        Write-Host "测试运行中 ($elapsed s)..." -ForegroundColor Yellow
        Write-Host "后台等待 pytest 完成..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "测试执行失败: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 总览完成 ===" -ForegroundColor Cyan
Write-Host "耗时: $((Get-Date) - $ts)" -ForegroundColor White
