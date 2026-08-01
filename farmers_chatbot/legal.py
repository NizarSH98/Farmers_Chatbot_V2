'''Versioned lifecycle-wide user agreement and privacy policy content.'''

from __future__ import annotations

from pathlib import Path

from .config import (
    APP_DISPLAY_NAME,
    CONSENT_VERSION,
    ORGANIZATION_NAME,
    PRIVACY_CONTACT_EMAIL,
    RETENTION_DAYS,
)

LEGAL_ROOT = Path(__file__).resolve().parents[1] / 'legal'


def _render_template(filename: str) -> str:
    template = (LEGAL_ROOT / filename).read_text(encoding='utf-8')
    replacements = {
        '{{APP_NAME}}': APP_DISPLAY_NAME,
        '{{LEGAL_VERSION}}': CONSENT_VERSION,
        '{{OPERATOR}}': ORGANIZATION_NAME,
        '{{PRIVACY_CONTACT}}': PRIVACY_CONTACT_EMAIL,
        '{{RETENTION_DAYS}}': str(RETENTION_DAYS),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    if '{{' in template or '}}' in template:
        raise RuntimeError(f'Unresolved legal-template marker in {filename}')
    return template.strip()


def agreement_markdown() -> str:
    '''Return the English project user agreement.'''

    return _render_template('USER_AGREEMENT.en.md')


def agreement_markdown_ar() -> str:
    '''Return the Arabic project user agreement.'''

    return _render_template('USER_AGREEMENT.ar.md')


def privacy_policy_markdown() -> str:
    '''Return the English project privacy policy.'''

    return _render_template('PRIVACY_POLICY.en.md')


def privacy_policy_markdown_ar() -> str:
    '''Return the Arabic project privacy policy.'''

    return _render_template('PRIVACY_POLICY.ar.md')


def whatsapp_consent_message() -> str:
    '''Return a short notice before a WhatsApp question is persisted.'''

    return (
        f'{APP_DISPLAY_NAME} privacy notice:\n'
        f'Messages are retained for up to {RETENTION_DAYS} days. Relevant content '
        'may be sent to configured AI providers. Do not send sensitive or '
        'confidential information. Verify high-risk advice with a professional.\n'
        f'Privacy contact: {PRIVACY_CONTACT_EMAIL}\n\n'
        'Reply AGREE to accept the User Agreement and acknowledge the Privacy '
        'Policy.\n\n'
        'إشعار الخصوصية: قد نحتفظ بالرسائل ونرسل المحتوى ذا الصلة إلى مزوّدي '
        'الذكاء الاصطناعي المعتمدين. لا ترسل معلومات حساسة أو سرية. أرسل AGREE '
        'لقبول اتفاقية الاستخدام والإقرار بسياسة الخصوصية.'
    )
