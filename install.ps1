# One-line setup for the CSAI club RAG demo (Windows). Paste this into PowerShell:
#
#   powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/tuffling/csai-rag-demo/main/install.ps1 | iex"
#
# It installs uv (which installs Python for you), downloads the demo into
# C:\Users\<you>\csai-rag-demo, and starts it. Paste the same line again any time to start the demo again.
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # makes downloads much faster in Windows PowerShell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RepoZip = "https://github.com/tuffling/csai-rag-demo/archive/refs/heads/main.zip"
$Dest = Join-Path $HOME "csai-rag-demo"

$env:Path = "$HOME\.local\bin;$env:Path"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$HOME\.local\bin;$env:Path"
}

if (Test-Path (Join-Path $Dest "rag.py")) {
    Write-Host "==> Found the demo in $Dest (keeping any changes you made)"
} else {
    Write-Host "==> Downloading the demo into $Dest ..."
    $Tmp = Join-Path ([IO.Path]::GetTempPath()) ("csai-rag-" + [Guid]::NewGuid())
    New-Item -ItemType Directory $Tmp | Out-Null
    Invoke-WebRequest $RepoZip -OutFile "$Tmp\demo.zip" -UseBasicParsing
    Expand-Archive "$Tmp\demo.zip" -DestinationPath $Tmp
    Move-Item "$Tmp\csai-rag-demo-main" $Dest
    Remove-Item -Recurse -Force $Tmp
}

Set-Location $Dest
Write-Host "==> Starting the demo (the first run downloads ~150 MB, hang tight)..."
if ($env:CI) { uv run rag.py --setup } else { uv run rag.py }
