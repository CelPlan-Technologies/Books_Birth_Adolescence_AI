# Listing 32.1 — Ollama settings (PowerShell)
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 32.2. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
#
# Complete version of Listing 32.1, in two steps, because a running Ollama
# reads its settings only when it starts:
#
#   .\ollama-env.ps1 -Setup   once: store the settings for the user (as setx
#                             does) and in this window; then quit Ollama from
#                             the tray icon and start it again
#   .\ollama-env.ps1 -Pull    after the restart: pull the models and record
#                             their digests
#
# setx (or [Environment]::SetEnvironmentVariable(..., 'User')) changes only
# the environment of processes started later; the current window and the
# running Ollama keep the old values. -Setup therefore also sets $env: here,
# and -Pull refuses to run until Ollama reports the expected model folder.
[CmdletBinding()]
param([switch]$Setup, [switch]$Pull)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$settings = [ordered]@{
  OLLAMA_MODELS          = 'D:\Box\models'
  OLLAMA_HOST            = '127.0.0.1:11434'   # loopback only: no key on Ollama
  OLLAMA_CONTEXT_LENGTH  = '32768'
  OLLAMA_FLASH_ATTENTION = '1'
  OLLAMA_KV_CACHE_TYPE   = 'q8_0'
  OLLAMA_KEEP_ALIVE      = '30m'
  OLLAMA_NUM_PARALLEL    = '2'
  OLLAMA_NO_CLOUD        = '1'
}
$models = @('gpt-oss:20b', 'qwen3-embedding:0.6b')

if ($Setup.IsPresent -eq $Pull.IsPresent) {
  Write-Host 'Usage: .\ollama-env.ps1 -Setup   (then restart Ollama)'
  Write-Host '       .\ollama-env.ps1 -Pull    (after the restart)'
  exit 2
}

if ($Setup) {
  New-Item -ItemType Directory -Force -Path $settings.OLLAMA_MODELS | Out-Null
  foreach ($name in $settings.Keys) {
    # persistent for the user (what setx does) ...
    [Environment]::SetEnvironmentVariable($name, $settings[$name], 'User')
    # ... and for this window, so that the next commands see it
    Set-Item -Path "env:$name" -Value $settings[$name]
  }
  Write-Host 'Settings stored. Now quit Ollama from the tray icon (Quit Ollama),'
  Write-Host 'start it again from the Start menu, then run: .\ollama-env.ps1 -Pull'
  exit 0
}

# -Pull: only after Ollama was restarted with the new settings
foreach ($name in $settings.Keys) {          # a new window reads the user values
  if (-not (Test-Path "env:$name")) {
    Set-Item -Path "env:$name" -Value ([Environment]::GetEnvironmentVariable($name, 'User'))
  }
}
try {
  $null = Invoke-RestMethod -Uri "http://$($settings.OLLAMA_HOST)/api/version" -TimeoutSec 5
} catch {
  throw "Ollama does not answer on $($settings.OLLAMA_HOST); start it and retry."
}
foreach ($m in $models) {
  ollama pull $m
  if ($LASTEXITCODE -ne 0) { throw "ollama pull $m failed" }
}
# The models must be in the new folder; if not, Ollama was not restarted.
$manifests = Join-Path $settings.OLLAMA_MODELS 'manifests'
if (-not (Test-Path $manifests)) {
  throw "No models in $($settings.OLLAMA_MODELS): restart Ollama so that it reads OLLAMA_MODELS, then pull again."
}
# Record what was installed (name, digest) with the Box's release record.
ollama list | Tee-Object -FilePath (Join-Path $settings.OLLAMA_MODELS 'installed-models.txt')
ollama ps    # what is loaded, CPU/GPU split
