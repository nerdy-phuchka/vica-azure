$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
if(-not (Test-Path -LiteralPath '.env')) {
  $content=Get-Content -LiteralPath '02_Configuration/.env.example' -Raw
  foreach($placeholder in @('replace-with-a-long-local-only-secret','replace-with-another-long-local-secret','replace-with-an-independent-long-secret')) {
    $bytes=New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $content=$content.Replace($placeholder,[Convert]::ToHexString($bytes))
  }
  [System.IO.File]::WriteAllText((Join-Path $root '.env'),$content)
  Write-Host 'Created local .env with independent random development secrets. Read DEV_AUTH_TOKEN locally to sign in; do not share it.'
} else {Write-Host 'Existing .env preserved.'}
docker compose config --quiet
if($LASTEXITCODE -ne 0){throw 'Docker Compose configuration failed.'}
docker compose up --build -d
if($LASTEXITCODE -ne 0){throw 'Container build/start failed. Check Docker and internet access.'}
Write-Host 'Open http://127.0.0.1:3000 . Use synthetic cases with local identity.'
