'''Static fail-closed checks for deployment inputs.'''

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tracked_files() -> set[str]:
    result = subprocess.run(
        ['git', 'ls-files'],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip().replace('\\', '/') for line in result.stdout.splitlines()}


def main() -> int:
    errors: list[str] = []
    tracked = tracked_files()
    forbidden = {
        '.env',
        '.streamlit/secrets.toml',
        'RAISE_Logframe_final.xlsx',
    }
    exposed = forbidden & tracked
    if exposed:
        errors.append('Sensitive/local files are tracked: ' + ', '.join(sorted(exposed)))

    required = {
        '.github/workflows/ci.yml',
        'alembic.ini',
        'compose.override.yaml',
        'compose.yaml',
        'Dockerfile.api',
        'Dockerfile.backup',
        'deploy/backup/backup.sh',
        'deploy/backup/restore.sh',
        'docs/DEPLOYMENT.md',
        'docs/README.md',
        'docs/product/PRODUCT_EXPERIENCE_SPEC.md',
        'farmers_chatbot/legal.py',
        'farmers_chatbot/oidc_auth.py',
        'legal/PRIVACY_POLICY.ar.md',
        'legal/PRIVACY_POLICY.en.md',
        'legal/USER_AGREEMENT.ar.md',
        'legal/USER_AGREEMENT.en.md',
        'migrations/001_pilot_schema.sql',
        'migrations/env.py',
        'migrations/versions/20260811_0001_legacy_schema_baseline.py',
        'migrations/versions/20260901_0007_provider_neutral_identity.py',
        'migrations/versions/20261110_0008_participant_codes.py',
        'requirements.txt',
        'scripts/pilot_data_portability.py',
        'docs/DATA_PORTABILITY.md',
        'docs/POLICY_APPROVAL_CHECKLIST.md',
    }
    missing = [path for path in sorted(required) if not (ROOT / path).is_file()]
    if missing:
        errors.append('Required release files are missing: ' + ', '.join(missing))

    obsolete = {
        'render.yaml',
        'farmers_chatbot/supabase_auth.py',
        'apps/web/lib/supabase.ts',
        'apps/web/app/auth/callback/route.ts',
    }
    present_obsolete = [path for path in sorted(obsolete) if (ROOT / path).exists()]
    if present_obsolete:
        errors.append(
            'Obsolete provider deployment files remain: '
            + ', '.join(present_obsolete)
        )

    compose = (ROOT / 'compose.yaml').read_text(encoding='utf-8')
    for contract in (
        'internal: true',
        'condition: service_completed_successfully',
        'QDRANT__TELEMETRY_DISABLED',
        'RESTIC_REPOSITORY',
        'profiles: ["tools"]',
    ):
        if contract not in compose:
            errors.append(f'Production Compose contract is missing {contract}.')
    if 'ports:' in compose:
        errors.append('Production Compose must not publish container ports directly.')

    api_dockerfile = (ROOT / 'Dockerfile.api').read_text(encoding='utf-8')
    if 'alembic upgrade head' in api_dockerfile:
        errors.append('API startup must not apply database migrations implicitly.')

    workflow = (ROOT / '.github/workflows/ci.yml').read_text(encoding='utf-8')
    for contract in ('ghcr.io/', 'type=sha,prefix=sha-', 'DOKPLOY_DEPLOY_WEBHOOK'):
        if contract not in workflow:
            errors.append(f'Container publication workflow is missing {contract}.')

    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    if 'alembic>=' not in requirements:
        errors.append('Alembic must be installed as a runtime deployment dependency.')

    secrets = (ROOT / '.env.example').read_text(encoding='utf-8')
    for key in (
        'APP_ENV',
        'APP_DISPLAY_NAME',
        'WEB_AUTH_MODE',
        'CONSENT_VERSION',
        'RETENTION_DAYS',
        'RESEARCH_RETENTION_DAYS',
        'DATABASE_URL',
        'OPENROUTER_ALLOWED_MODELS',
        'OPENROUTER_DEFAULT_MODEL',
        'OPENROUTER_ENFORCE_ZDR',
        'PRIVACY_CONTACT_EMAIL',
        'OIDC_ISSUER_URL',
        'OIDC_CLIENT_ID',
        'APP_SESSION_SECRET',
        'STORAGE_BACKEND',
        'S3_BUCKET',
        'RESTIC_REPOSITORY',
        'RESTIC_PASSWORD',
        'QDRANT_API_KEY',
    ):
        if key not in secrets:
            errors.append(f'Environment template is missing {key}.')

    if errors:
        print('Pilot release preflight failed:')
        for error in errors:
            print(f'- {error}')
        return 1
    print('Pilot release preflight passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
