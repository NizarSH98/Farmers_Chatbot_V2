"""One-release import wrapper for the canonical FastAPI WhatsApp router.

Deploy farmers_chatbot.web_api:app. This module remains temporarily so old
commands importing whatsapp_api:app reach that same application.
"""

from farmers_chatbot.web_api import app
from farmers_chatbot.whatsapp_router import (
    receive_whatsapp_webhook,
    router,
    verify_whatsapp_webhook,
    whatsapp_healthz,
)

__all__ = [
    "app",
    "receive_whatsapp_webhook",
    "router",
    "verify_whatsapp_webhook",
    "whatsapp_healthz",
]
