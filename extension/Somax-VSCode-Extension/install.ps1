$ErrorActionPreference = "Stop"
$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$destination = Join-Path $env:USERPROFILE ".vscode\extensions\somax.somax-language-0.1.0"
$parent = Split-Path -Parent $destination
New-Item -ItemType Directory -Force -Path $parent | Out-Null
if (Test-Path $destination) {
    Remove-Item -Recurse -Force $destination
}
Copy-Item -Recurse -Force $source $destination
Write-Host "Somax VS Code extension installed to $destination"
Write-Host "Restart VS Code or run Developer: Reload Window."
