import pytest

from app.modules.catalog.service import MAX_IMAGE_BYTES, validate_image_upload


def test_rejects_image_larger_than_ten_mib():
    with pytest.raises(ValueError, match="不能超过 10 MiB"):
        validate_image_upload("sample.png", "image/png", b"x" * (MAX_IMAGE_BYTES + 1))


def test_storage_suffix_comes_from_verified_mime_not_original_path():
    suffix = validate_image_upload("../../outside.exe", "image/png", b"png")

    assert suffix == ".png"
