[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'logs', 'build-graph', 'evaluate', 'snapshot', 'export', 'restore', 'smoke')]
    [string]$Command = 'status',
    [string]$Path = '',
    [switch]$Rebuild
)

$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $ProjectRoot 'compose.yaml'
$BackupRoot = Join-Path $ProjectRoot 'backups'

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & docker compose -f $Compose @Arguments
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed with exit code $LASTEXITCODE" }
}

function Invoke-LocalPython {
    param(
        [Parameter(Mandatory = $true)][string]$Module,
        [string[]]$Arguments = @()
    )
    $oldDatabaseUrl = $env:DATABASE_URL
    $oldQdrantUrl = $env:QDRANT_URL
    $oldModelCache = $env:RAG_MODEL_CACHE
    $oldPythonUtf8 = $env:PYTHONUTF8
    $localPassword = if ($env:RAISE_LOCAL_DB_PASSWORD) { $env:RAISE_LOCAL_DB_PASSWORD } else { 'raise-local-only' }
    $encodedPassword = [Uri]::EscapeDataString($localPassword)
    try {
        $env:DATABASE_URL = "postgresql://raise:${encodedPassword}@127.0.0.1:55432/raise"
        $env:QDRANT_URL = 'http://127.0.0.1:6433'
        $env:RAG_MODEL_CACHE = Join-Path $ProjectRoot 'model-cache'
        $env:PYTHONUTF8 = '1'
        Push-Location $ProjectRoot
        & python -m $Module @Arguments
        if ($LASTEXITCODE -ne 0) { throw "$Module failed with exit code $LASTEXITCODE" }
    }
    finally {
        Pop-Location
        $env:DATABASE_URL = $oldDatabaseUrl
        $env:QDRANT_URL = $oldQdrantUrl
        $env:RAG_MODEL_CACHE = $oldModelCache
        $env:PYTHONUTF8 = $oldPythonUtf8
    }
}

function New-ReleaseSnapshot {
    New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $target = Join-Path $BackupRoot "raise-$stamp"
    New-Item -ItemType Directory -Force -Path $target | Out-Null
    Invoke-Compose exec -T postgres pg_dump -U raise -d raise -Fc -f /tmp/raise-postgres.dump
    $postgresContainer = (& docker compose -f $Compose ps -q postgres).Trim()
    if (-not $postgresContainer) { throw 'PostgreSQL container is not running.' }
    & docker cp "${postgresContainer}:/tmp/raise-postgres.dump" (Join-Path $target 'postgres.dump')
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy PostgreSQL dump.' }
    Invoke-LocalPython -Module 'scripts.snapshot_qdrant' -Arguments @('--output', (Join-Path $target 'qdrant-snapshots.json'))
    $files = Get-ChildItem -LiteralPath $target -Recurse -File | ForEach-Object {
        [ordered]@{
            path = $_.FullName.Substring($target.Length + 1).Replace('\', '/')
            sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            bytes = $_.Length
        }
    }
    $handoff = [ordered]@{
        schema_version = 'raise.local-handoff.v1'
        created_at = (Get-Date).ToUniversalTime().ToString('o')
        migration_revision = '20260812_0005'
        files = @($files)
    }
    $handoff | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $target 'handoff-manifest.json') -Encoding utf8
    Write-Output $target
}

switch ($Command) {
    'start' {
        $arguments = @('up', '-d')
        if ($Rebuild) { $arguments += '--build' }
        Invoke-Compose @arguments
        Invoke-Compose ps
    }
    'stop' { Invoke-Compose down }
    'status' { Invoke-Compose ps }
    'logs' { Invoke-Compose logs --tail 200 api web postgres qdrant }
    'build-graph' { Invoke-LocalPython -Module 'scripts.build_graph_release' -Arguments @('--activate') }
    'evaluate' { Invoke-LocalPython -Module 'scripts.run_local_evaluation' -Arguments @('--split', 'public') }
    'snapshot' { New-ReleaseSnapshot }
    'export' { New-ReleaseSnapshot }
    'restore' {
        if (-not $Path) { throw 'restore requires -Path <backup-directory>' }
        $resolved = (Resolve-Path -LiteralPath $Path).Path
        if (-not (Test-Path -LiteralPath $BackupRoot)) { throw 'The project backup directory does not exist.' }
        if (-not $resolved.StartsWith((Resolve-Path $BackupRoot).Path, [StringComparison]::OrdinalIgnoreCase)) {
            throw 'Restore source must be inside the project backups directory.'
        }
        $postgresDump = Join-Path $resolved 'postgres.dump'
        $qdrantManifest = Join-Path $resolved 'qdrant-snapshots.json'
        if (-not (Test-Path -LiteralPath $postgresDump) -or -not (Test-Path -LiteralPath $qdrantManifest)) { throw 'Backup is incomplete.' }
        $postgresContainer = (& docker compose -f $Compose ps -q postgres).Trim()
        if (-not $postgresContainer) { throw 'PostgreSQL container is not running.' }
        & docker cp $postgresDump "${postgresContainer}:/tmp/raise-postgres.dump"
        if ($LASTEXITCODE -ne 0) { throw 'Could not copy PostgreSQL dump.' }
        & docker compose -f $Compose exec -T postgres pg_restore -U raise --dbname=raise --clean --if-exists /tmp/raise-postgres.dump
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL restore failed.' }
        Invoke-LocalPython -Module 'scripts.restore_qdrant' -Arguments @('--manifest', $qdrantManifest, '--replace')
        Invoke-LocalPython -Module 'scripts.local_smoke_test'
    }
    'smoke' {
        Invoke-Compose exec -T api python -m scripts.local_smoke_test
    }
}
