# 项目完整性快速检查
$ErrorActionPreference = 'SilentlyContinue'
$ROOT = "D:\meetgrow-agent-skill"
$PY = "C:\Users\52637\miniconda3\envs\meetgrow\python.exe"

Write-Host "=== MEETGROW 项目状态 ===" -ForegroundColor Cyan
Write-Host ""

# 1. 目录检查
$dirs = @("meetgrow_skill/core", "meetgrow_skill/tools", "examples", "tests", "docs")
foreach ($d in $dirs) {
    $p = Join-Path $ROOT $d
    if (Test-Path $p) {
        $n = (Get-ChildItem $p -Recurse -File -Filter "*.py").Count
        Write-Host "  ✅ $d/ ($n py)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $d/ MISSING" -ForegroundColor Red
    }
}

# 2. 文件检查
$req = @(
    "README.md","README_zh.md","publish_skill.py",
    "meetgrow_skill/__init__.py","meetgrow_skill/skill.py",
    "meetgrow_skill/__main__.py","meetgrow_skill/config.py",
    "meetgrow_skill/core/agent.py","meetgrow_skill/core/orchestrator.py",
    "meetgrow_skill/core/memory.py",
    "meetgrow_skill/tools/base.py",
    "meetgrow_skill/tools/ocr_tool.py","meetgrow_skill/tools/asr_tool.py",
    "meetgrow_skill/tools/tts_tool.py","meetgrow_skill/tools/doc_tool.py",
    "examples/demo_card_ocr.py","examples/demo_meeting_minutes.py",
    "docs/tech_article.md"
)
foreach ($f in $req) {
    $p = Join-Path $ROOT $f
    if (Test-Path $p) {
        Write-Host "  ✅ $f" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $f MISSING" -ForegroundColor Red
    }
}

# 3. 统计
$pyFiles = Get-ChildItem $ROOT -Recurse -Filter "*.py" -File
$testFiles = Get-ChildItem $ROOT -Filter "test_*.py" -File
Write-Host ""
Write-Host "Python files: $($pyFiles.Count)"
Write-Host "Test files: $($testFiles.Count)"

# 4. 文章
$article = Join-Path $ROOT "docs/tech_article.md"
if (Test-Path $article) {
    $len = (Get-Item $article).Length
    Write-Host "Tech article: $len bytes" -ForegroundColor Green
}

# 5. JSON/ZIP
$json = Get-ChildItem $ROOT -Filter "*.json" -File
$zip = Get-ChildItem $ROOT -Filter "*.zip" -File
foreach ($f in $json) { Write-Host "JSON: $($f.Name) ($($f.Length)B)" }
foreach ($f in $zip) { Write-Host "ZIP: $($f.Name) ($($f.Length)B)" }

# 6. 快速 pytest (120s timeout)
Write-Host ""
Write-Host "Running pytest..." -ForegroundColor Yellow
$result = $null
$ts = Get-Date
try {
    $p = Start-Process $PY -ArgumentList @("-m","pytest","tests/","-v","--tb=short","-q","-W","ignore","-W","ignore::DeprecationWarning") `
        -WorkingDirectory $ROOT -NoNewWindow -PassThru
    # 等待最多120秒
    $waited = 0
    while ($waited -lt 120 -and -not $p.HasExited) {
        Start-Sleep -Seconds 5
        $waited += 5
    }
    if ($p.HasExited) {
        # 输出结果
        $out = & $PY -m pytest tests/ -v --tb=short -q -W ignore -W ignore::DeprecationWarning 2>&1
        $out
    } else {
        Write-Host "Test still running... will check later" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}

$elapsed = ((Get-Date) - $ts).TotalSeconds
Write-Host ""
Write-Host "Done in ${elapsed}s" -ForegroundColor Cyan
