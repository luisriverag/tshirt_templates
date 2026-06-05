from io import BytesIO

from tshirt_templates.uploads import is_allowed_upload, list_uploaded_badges, save_uploaded_badges


class FakeUpload(BytesIO):
    def __init__(self, filename: str, content: bytes):
        super().__init__(content)
        self.filename = filename

    def save(self, destination):
        with open(destination, "wb") as output:
            output.write(self.getvalue())


def test_is_allowed_upload_accepts_supported_images_only():
    assert is_allowed_upload("badge.svg")
    assert is_allowed_upload("badge.PNG")
    assert is_allowed_upload("photo.jpeg")
    assert not is_allowed_upload("notes.pdf")


def test_save_uploaded_badges_persists_and_lists_files(tmp_path):
    saved = save_uploaded_badges(
        [FakeUpload("my badge.svg", b"<svg></svg>"), FakeUpload("notes.txt", b"nope")],
        tmp_path,
    )

    assert len(saved) == 1
    assert saved[0].id.startswith("upload:")
    assert saved[0].name == "My Badge"
    assert saved[0].raw_url.startswith("/uploads/")
    assert saved[0].local_path is not None

    listed = list_uploaded_badges(tmp_path)

    assert listed == saved
