import base64
import io

from PIL import Image

from farmers_chatbot.auth import UserIdentity
from farmers_chatbot.storage_backends import LocalPrivateStorage
from farmers_chatbot.streamlit_app import _prepare_chat_image


class Upload:
    name = "field-photo.jpg"
    type = "image/jpeg"

    def __init__(self, data: bytes):
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


def test_chat_image_is_resized_and_metadata_is_removed(tmp_path):
    original = Image.new("RGB", (2400, 1200), "green")
    exif = Image.Exif()
    exif[0x010E] = "private field location"
    source = io.BytesIO()
    original.save(source, format="JPEG", exif=exif)

    identity = UserIdentity(
        user_id="user-1",
        issuer="https://accounts.google.com",
        subject="subject-1",
        email="tester@example.org",
        name="Tester",
        is_admin=False,
    )
    storage = LocalPrivateStorage(tmp_path / "private")
    persisted, model_input = _prepare_chat_image(
        identity,
        "conversation-1",
        Upload(source.getvalue()),
        storage,
    )

    stored = storage.get(persisted["storage_path"])
    encoded = model_input["data_url"].split(",", 1)[1]
    assert stored == base64.b64decode(encoded)
    with Image.open(io.BytesIO(stored)) as cleaned:
        assert cleaned.width <= 2048
        assert cleaned.height <= 2048
        assert not cleaned.getexif()
