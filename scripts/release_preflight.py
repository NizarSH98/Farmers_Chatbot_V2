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
        'deployment/streamlit_secrets.toml.example',
        'farmers_chatbot/legal.py',
        'legal/PRIVACY_POLICY.ar.md',
        'legal/PRIVACY_POLICY.en.md',
        'legal/USER_AGREEMENT.ar.md',
        'legal/USER_AGREEMENT.en.md',
        'migrations/001_pilot_schema.sql',
        'rag_chatbot.py',
        'render.yaml',
        'requirements.txt',
        'scripts/pilot_data_portability.py',
        'docs/DATA_PORTABILITY.md',
        'docs/POLICY_APPROVAL_CHECKLIST.md',
    }
    missing = [path for path in sorted(required) if not (ROOT / path).is_file()]
    if missing:
        errors.append('Required release files are missing: ' + ', '.join(missing))

    render = (ROOT / 'render.yaml').read_text(encoding='utf-8')
    if 'autoDeploy: false' not in render or 'plan: starter' not in render:
        errors.append('Render must use the paid starter plan with autoDeploy disabled.')

    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
    if 'streamlit==' not in requirements:
        errors.append('Pin Streamlit exactly for reproducible Community Cloud builds.')

    secrets = (ROOT / 'deployment/streamlit_secrets.toml.example').read_text(
        encoding='utf-8'
    )
    for key in (
        'APP_ENV',
        'APP_DISPLAY_NAME',
        'AUTH_MODE',
        'CONSENT_VERSION',
        'DATABASE_URL',
        'OPENROUTER_ALLOWED_MODELS',
        'OPENROUTER_DEFAULT_MODEL',
        'OPENROUTER_ENFORCE_ZDR',
        'PRIVACY_CONTACT_EMAIL',
        'SUPABASE_SERVICE_ROLE_KEY',
    ):
        if key not in secrets:
            errors.append(f'Managed secrets template is missing {key}.')

    if errors:
        print('Pilot release preflight failed:')
        for error in errors:
            print(f'- {error}')
        return 1
    print('Pilot release preflight passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
