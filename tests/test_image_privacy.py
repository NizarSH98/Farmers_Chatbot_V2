import io

from PIL import Image

from farmers_chatbot.image_processing import sanitize_chat_image


def _jpeg_with_exif(width: int, height: int) -> bytes:
    original = Image.new("RGB", (width, height), "green")
    exif = Image.Exif()
    exif[0x010E] = "private field location"
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", exif=exif)
    return buffer.getvalue()


def test_chat_image_is_resized_and_metadata_is_removed():
    sanitized = sanitize_chat_image(_jpeg_with_exif(2400, 1200), "image/jpeg")

    assert sanitized.mime_type == "image/jpeg"
    assert sanitized.width <= 2048
    assert sanitized.height <= 2048
    with Image.open(io.BytesIO(sanitized.data)) as cleaned:
        assert cleaned.width <= 2048
        assert cleaned.height <= 2048
        assert not cleaned.getexif()
