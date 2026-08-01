'''Versioned pilot user agreement and privacy notice content.'''

from __future__ import annotations

from .config import (
    CONSENT_VERSION,
    ORGANIZATION_NAME,
    PRIVACY_CONTACT_EMAIL,
    RETENTION_DAYS,
)


def agreement_markdown() -> str:
    '''Return the English pilot agreement and privacy notice.'''

    return f'''
### Pilot User Agreement and Privacy Notice

**Version:** `{CONSENT_VERSION}`

**Operator:** {ORGANIZATION_NAME}

**Privacy contact:** {PRIVACY_CONTACT_EMAIL}

This internal pilot supports agricultural, scientific, and rural-enterprise
decisions. It can be wrong and does not replace a qualified professional,
laboratory, authority, or emergency service.

We store your Google account identifier, verified email, display name, role,
consent record, and content you create: chats, project instructions, files,
images, artifacts, feedback, and limited usage metadata. We never ask for your
Google password. Do not submit identifiers, payment or health records, exact home
addresses, credentials, private phone numbers, confidential data, or other
sensitive personal information. Upload only material you may use.

Questions, limited recent context, relevant passages, and supplied images may be
sent to OpenRouter and a selected model provider. Online voice sends answer text
to Microsoft Edge TTS. This service uses Google, Streamlit, Supabase, OpenRouter
and model providers; optional WhatsApp also uses Meta and Render. Each provider
has its own terms.

Identifiable pilot content is retained for up to **{RETENTION_DAYS} days** by
default, then deleted or anonymized. Anonymous aggregate metrics may remain. You
can delete content, export workspace data, or delete your account. Provider
backups and security logs may expire later under provider policies. Contact
{PRIVACY_CONTACT_EMAIL} for privacy requests you cannot complete in the app.

Do not bypass access controls, upload malware, impersonate someone, violate law,
or use the pilot to harm people, animals, property, or the environment. Uploaded
documents are user-provided, not approved authority. Verify important outputs.
Material agreement changes require acceptance of a new version.
'''.strip()


def agreement_markdown_ar() -> str:
    '''Return the Arabic pilot agreement and privacy notice.'''

    return f'''
### اتفاقية استخدام النسخة التجريبية وإشعار الخصوصية

**الإصدار:** `{CONSENT_VERSION}`

**الجهة المشغّلة:** {ORGANIZATION_NAME}

**الخصوصية:** {PRIVACY_CONTACT_EMAIL}

هذه نسخة داخلية تجريبية لدعم القرارات الزراعية والعلمية والاقتصادية. قد تخطئ
ولا تحل محل المختص أو المختبر أو الجهة الرسمية أو الطوارئ. لا تعتمد عليها وحدها
في القرارات العاجلة أو عالية المخاطر.

نحفظ معرّف حساب Google والبريد المؤكد والاسم الظاهر ووقت وإصدار الموافقة، إضافة
إلى المحادثات والملفات والصور والمخرجات والتقييمات والبيانات التقنية المحدودة.
لا نحفظ كلمة مرور Google. لا ترسل أرقام الهوية أو الدفع أو السجلات الصحية أو
العنوان الدقيق أو كلمات المرور أو معلومات شخصية حساسة أو سرية.

قد يُرسل السؤال وسياق محدود والمقاطع ذات الصلة والصورة إلى OpenRouter ومقدم
النموذج. نستخدم Google وStreamlit وSupabase وOpenRouter، وتستخدم قناة WhatsApp
الاختيارية Meta وRender. لكل مزود سياسة خاصة به.

نحتفظ بالمحتوى المرتبط بك لمدة تصل إلى **{RETENTION_DAYS} يوماً** ثم نحذفه أو
نزيل ارتباطه بهويتك. قد تبقى مؤشرات مجهّلة. يمكنك حذف المحتوى وتنزيل نسخة أو
حذف الحساب. تواصل عبر {PRIVACY_CONTACT_EMAIL} لطلب لا تستطيع تنفيذه من التطبيق.

لا تتجاوز الحماية ولا ترفع ملفات ضارة أو مواد لا يحق لك استخدامها. الملفات
المرفوعة ليست مرجعاً رسمياً معتمداً. أي تغيير جوهري يتطلب موافقة جديدة.
'''.strip()


def whatsapp_consent_message() -> str:
    '''Return a short notice before a WhatsApp question is persisted.'''

    return (
        'RAISE internal AI pilot privacy notice:\n'
        f'Messages are retained for up to {RETENTION_DAYS} days and question '
        'content may be sent to AI providers. Do not send sensitive or confidential '
        'information. Verify high-risk advice with a professional.\n'
        f'Privacy contact: {PRIVACY_CONTACT_EMAIL}\n\n'
        'Reply AGREE to accept and start.\n\n'
        'إشعار الخصوصية: قد نحتفظ بالرسائل ونرسل السؤال إلى مزود الذكاء '
        'الاصطناعي. لا ترسل معلومات حساسة. أرسل AGREE للموافقة والبدء.'
    )
