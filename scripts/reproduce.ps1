# 从原文到四段 mp3 · 一键复现脚本
# 用法：.\reproduce.ps1 -Input .\chapter.txt -Out .\audio
param(
    [Parameter(Mandatory=$true)][string]$Input,
    [string]$Out = "./audio",
    [int]$MaxChars = 700,
    [double]$Gap = 3.0
)

$ErrorActionPreference = "Stop"

if (-not $env:BREEZE_API_KEY)  { throw "缺少 BREEZE_API_KEY，形如 brz_xxx" }
if (-not $env:BREEZE_TTS_VOICE) { throw "缺少 BREEZE_TTS_VOICE，形如 voc_xxxxxxxx" }

Write-Host "[1/4] 环境检查通过" -ForegroundColor Green
Write-Host "[2/4] 开始清洗 + 分段 + 合成（约 40 字/秒）"

python scripts/tts_batch.py --input $Input --out $Out --max-chars $MaxChars --gap $Gap
if ($LASTEXITCODE -ne 0) { throw "合成失败，退出码 $LASTEXITCODE" }

Write-Host "[3/4] 校验产物"
$files = Get-ChildItem "$Out\*.mp3" | Sort-Object Name
if ($files.Count -eq 0) { throw "没生成任何 mp3" }
foreach ($f in $files) {
    if ($f.Length -lt 50KB) { Write-Warning "$($f.Name) 只有 $([math]::Round($f.Length/1KB,0)) KB，疑似异常短" }
    Write-Host ("  {0}  {1:N2} MB" -f $f.Name, ($f.Length/1MB))
}

Write-Host "[4/4] 完成，清单：$Out\manifest.json" -ForegroundColor Green
Write-Host "提示：一段 500-700 字，场景切换处务必手动断段。"
