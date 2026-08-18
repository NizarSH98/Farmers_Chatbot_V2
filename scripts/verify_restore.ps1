[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Path
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Compose = Join-Path $ProjectRoot "compose.yaml"
$Override = Join-Path $ProjectRoot "compose.restore.yaml"
$BackupRoot = (Resolve-Path (Join-Path $ProjectRoot "backups")).Path
$Backup = (Resolve-Path -LiteralPath $Path).Path
$Project = "raise-restore"

if (-not $Backup.StartsWith($BackupRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Restore source must be inside the project backups directory."
}
$Dump = Join-Path $Backup "postgres.dump"
$Snapshots = Join-Path $Backup "qdrant-snapshots.json"
if (-not (Test-Path $Dump) -or -not (Test-Path $Snapshots)) {
    throw "Backup is incomplete."
}

function Compose {
    & docker compose -p $Project -f $Compose -f $Override @args
    if ($LASTEXITCODE -ne 0) { throw "docker compose failed with exit code $LASTEXITCODE" }
}

function Wait-Healthy([string[]]$Containers, [int]$Seconds = 240) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $states = @($Containers | ForEach-Object {
            (& docker inspect --format="{{.State.Health.Status}}" $_ 2>$null).Trim()
        })
        if (@($states | Where-Object { $_ -ne "healthy" }).Count -eq 0) { return }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Restore stack health timeout: $($states -join ', ')"
}

# The fixed project name makes this deletion apply only to the disposable verifier.
Compose down --volumes --remove-orphans
Compose up -d postgres qdrant
Wait-Healthy @("raise-restore-postgres-1", "raise-restore-qdrant-1")

& docker cp $Dump "raise-restore-postgres-1:/tmp/raise-postgres.dump"
if ($LASTEXITCODE -ne 0) { throw "Could not copy PostgreSQL dump." }
Compose exec -T postgres pg_restore -U raise --dbname=raise --clean --if-exists /tmp/raise-postgres.dump

$oldQdrant = $env:QDRANT_URL
try {
    $env:QDRANT_URL = "http://127.0.0.1:6434"
    Push-Location $ProjectRoot
    python -m scripts.restore_qdrant --manifest $Snapshots
    if ($LASTEXITCODE -ne 0) { throw "Qdrant snapshot restore failed." }
}
finally {
    Pop-Location
    $env:QDRANT_URL = $oldQdrant
}

Compose up -d --build api web
Wait-Healthy @("raise-restore-api-1", "raise-restore-web-1")

$oldDatabase = $env:DATABASE_URL
$oldQdrant = $env:QDRANT_URL
$oldCache = $env:RAG_MODEL_CACHE
$oldUtf8 = $env:PYTHONUTF8
try {
    $env:DATABASE_URL = "postgresql://raise:raise-local-only@127.0.0.1:55433/raise"
    $env:QDRANT_URL = "http://127.0.0.1:6434"
    $env:RAG_MODEL_CACHE = Join-Path $ProjectRoot "model-cache"
    $env:PYTHONUTF8 = "1"
    Push-Location $ProjectRoot
    python -m scripts.local_smoke_test
    if ($LASTEXITCODE -ne 0) { throw "Host restore smoke test failed." }
}
finally {
    Pop-Location
    $env:DATABASE_URL = $oldDatabase
    $env:QDRANT_URL = $oldQdrant
    $env:RAG_MODEL_CACHE = $oldCache
    $env:PYTHONUTF8 = $oldUtf8
}

Compose exec -T api python -m scripts.local_smoke_test
$health = Invoke-RestMethod -Uri "http://127.0.0.1:8001/healthz"
$web = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:3001/").StatusCode
$admin = (Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:3001/admin").StatusCode

[ordered]@{
    status = "verified"
    release_id = $health.active_release_id
    migration_revision = $health.migration_revision
    projection_status = $health.projection_status
    qdrant_reachable = $health.qdrant_reachable
    fallback_ready = $health.fallback_ready
    web_status = $web
    admin_status = $admin
    backup = $Backup
} | ConvertTo-Json
