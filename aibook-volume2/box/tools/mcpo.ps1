# Listing 32.3 — Local files as a tool (mcpo)
# From "The Birth and Adolescence of Artificial Intelligence", Volume 2, Section 32.5. Illustrative: checked against the documentation of the versions in Appendix B (Volume 2), not run end to end as one system. Test in staging before use.
# SPDX-License-Identifier: MIT
#
# Complete version of Listing 32.3, with setup and start separated:
#
#   .\mcpo.ps1 -Setup   once: a random key and a pinned server
#   .\mcpo.ps1 -Start   at sign-in (Task Scheduler) or in any window
#
# setx alone stores the key for processes started later, not for the window
# that ran it; -Setup sets both, and -Start reads the stored user value when
# the window has none, then refuses to start without a valid key.
#
# READ-ONLY REFERENCE DOCUMENTS. server-filesystem also offers write, edit
# and move tools, and a restricted directory is not a read-only one. If the
# reference folder must not change, enforce it with the operating system:
# run -Start under a separate local account that can only read the folder,
# for example
#   icacls D:\Box\docs\reference /grant "box-reader:(OI)(CI)RX"
# and a Task Scheduler task "Run as" box-reader, or keep D:\Box\docs\reference
# a copy that the indexer refreshes. Do not rely on the model's restraint.
[CmdletBinding()]
param([switch]$Setup, [switch]$Start)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$docs = 'D:\Box\docs\reference'

if ($Setup.IsPresent -eq $Start.IsPresent) {
  Write-Host 'Usage: .\mcpo.ps1 -Setup   (once)'
  Write-Host '       .\mcpo.ps1 -Start   (each sign-in)'
  exit 2
}

if ($Setup) {
  $key = [guid]::NewGuid().ToString('N')         # 32 hex digits
  [Environment]::SetEnvironmentVariable('MCPO_KEY', $key, 'User')   # like setx
  $env:MCPO_KEY = $key                            # and for this window
  npm install -g `
    @modelcontextprotocol/server-filesystem@2026.1.14
  if ($LASTEXITCODE -ne 0) { throw 'npm install failed' }
  uv tool install --python 3.11 mcpo==0.0.20
  if ($LASTEXITCODE -ne 0) { throw 'uv tool install failed' }
  Write-Host 'Setup done. Enter the key in Open WebUI (below); start with .\mcpo.ps1 -Start'
  exit 0
}

# -Start
if (-not $env:MCPO_KEY) {
  $env:MCPO_KEY = [Environment]::GetEnvironmentVariable('MCPO_KEY', 'User')
}
if (-not $env:MCPO_KEY -or $env:MCPO_KEY -notmatch '^[0-9a-f]{32,}$') {
  throw 'MCPO_KEY is missing or not a 32-hex-digit key; run .\mcpo.ps1 -Setup first.'
}
if (-not (Test-Path $docs)) { throw "$docs does not exist" }
mcpo --host 127.0.0.1 --port 8000 `
  --api-key $env:MCPO_KEY -- `
  mcp-server-filesystem $docs
# Open WebUI: add an OpenAPI tool server at
#   http://127.0.0.1:8000, with the same key
