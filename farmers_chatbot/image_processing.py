"""Shared, bounded chat-image sanitation for every RAISE channel."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import MAX_CHAT_IMAGE_BYTES

SUPPORTED_IMAGE_MIME_TYPES = frozenset({"image/jpeg", "image/png"})
MAX_CHAT_IMAGE_PIXELS = 24_000_000
MAX_CHAT_IMAGE_DIMENSION = 2048


class InvalidChatImage(ValueError):
    """Raised when an uploaded image is unsupported, invalid, or unsafe."""


@dataclass(frozen=True)
class SanitizedChatImage:
    data: bytes
    mime_type: str
    extension: str
    width: int
    height: int


def sanitize_chat_image(
    data: bytes,
    supplied_mime: str,
    *,
    max_input_bytes: int = MAX_CHAT_IMAGE_BYTES,
    max_output_bytes: int = MAX_CHAT_IMAGE_BYTES,
    max_pixels: int = MAX_CHAT_IMAGE_PIXELS,
    max_dimension: int = MAX_CHAT_IMAGE_DIMENSION,
) -> SanitizedChatImage:
    """Validate, orient, downscale, and re-encode an untrusted chat image."""

    mime_type = supplied_mime.split(";", 1)[0].strip().lower()
    if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
        raise InvalidChatImage("Only JPG and PNG are accepted")
    if not data or len(data) > max_input_bytes:
        raise InvalidChatImage("Image input size is outside the allowed range")
    try:
        with Image.open(io.BytesIO(data)) as opened:
            actual_mime = Image.MIME.get(opened.format or "", "")
            if actual_mime not in SUPPORTED_IMAGE_MIME_TYPES:
                raise InvalidChatImage("Image content is not JPG or PNG")
            if opened.width <= 0 or opened.height <= 0:
                raise InvalidChatImage("Image dimensions are invalid")
            if opened.width * opened.height > max_pixels:
                raise InvalidChatImage("Image pixel count is too large")
            opened.load()
            cleaned = ImageOps.exif_transpose(opened)
            cleaned.thumbnail(
                (max_dimension, max_dimension),
                Image.Resampling.LANCZOS,
            )
            output = io.BytesIO()
            has_alpha = cleaned.mode in {"RGBA", "LA"} or (
                cleaned.mode == "P" and "transparency" in cleaned.info
            )
            if actual_mime == "image/png" and has_alpha:
                cleaned.convert("RGBA").save(output, format="PNG", optimize=True)
                stored_mime = "image/png"
                extension = "png"
            else:
                cleaned.convert("RGB").save(
                    output,
                    format="JPEG",
                    quality=88,
                    optimize=True,
                )
                stored_mime = "image/jpeg"
                extension = "jpg"
            sanitized = output.getvalue()
            width, height = cleaned.size
    except InvalidChatImage:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:
        raise InvalidChatImage("Image is invalid or unsafe") from exc
    if not sanitized or len(sanitized) > max_output_bytes:
        raise InvalidChatImage("Sanitized image is too large")
    return SanitizedChatImage(
        data=sanitized,
        mime_type=stored_mime,
        extension=extension,
        width=width,
        height=height,
    )
