[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('start', 'stop', 'status', 'logs', 'build-graph', 'evaluate', 'ablate', 'graph-profile', 'snapshot', 'export', 'restore', 'smoke', 'archive')]
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

function Invoke-ContainerPython {
    # Data commands run inside the API container so the local workflow uses the
    # same interpreter, dependencies, and network as the deployed service. It
    # also removes any dependency on a host Python or a published database port.
    param(
        [Parameter(Mandatory = $true)][string]$Module,
        [string[]]$Arguments = @()
    )
    Invoke-Compose exec -T api sh -c "cd /app && python -m $Module $($Arguments -join ' ')"
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
    Invoke-ContainerPython -Module 'scripts.snapshot_qdrant' -Arguments @('--output', '/tmp/qdrant-snapshots.json')
    $apiContainer = (& docker compose -f $Compose ps -q api).Trim()
    if (-not $apiContainer) { throw 'API container is not running.' }
    & docker cp "${apiContainer}:/tmp/qdrant-snapshots.json" (Join-Path $target 'qdrant-snapshots.json')
    if ($LASTEXITCODE -ne 0) { throw 'Could not copy the Qdrant snapshot manifest.' }
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
        migration_revision = '20260819_0006'
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
    'build-graph' { Invoke-ContainerPython -Module 'scripts.build_graph_release' -Arguments @('--activate') }
    'evaluate' { Invoke-ContainerPython -Module 'scripts.run_local_evaluation' -Arguments @('--split', 'public') }
    'ablate' { Invoke-ContainerPython -Module 'scripts.run_ablations' }
    'graph-profile' { Invoke-ContainerPython -Module 'scripts.profile_graph' }
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
        $apiContainer = (& docker compose -f $Compose ps -q api).Trim()
        if (-not $apiContainer) { throw 'API container is not running.' }
        & docker cp $qdrantManifest "${apiContainer}:/tmp/qdrant-snapshots.json"
        if ($LASTEXITCODE -ne 0) { throw 'Could not copy the Qdrant snapshot manifest.' }
        Invoke-ContainerPython -Module 'scripts.restore_qdrant' -Arguments @('--manifest', '/tmp/qdrant-snapshots.json', '--replace')
        Invoke-ContainerPython -Module 'scripts.local_smoke_test'
    }
    'smoke' { Invoke-ContainerPython -Module 'scripts.local_smoke_test' }
    'archive' {
        if (-not $Path) { throw 'archive requires -Path <output-directory-inside-container>' }
        Invoke-ContainerPython -Module 'scripts.archive_user_data' -Arguments @('--output', $Path)
    }
}
