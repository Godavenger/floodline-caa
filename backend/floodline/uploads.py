from __future__ import annotations

import io
import warnings
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from .service import DomainError

MAX_PIXELS = 12_000_000


def clean_image(content: bytes, limit: int) -> bytes:
    if len(content) > limit:
        raise DomainError(413, "The image exceeds the 5 MB upload limit.")
    if not content:
        raise DomainError(422, "The attachment is empty.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as original:
                if original.format not in ("JPEG", "PNG", "WEBP"):
                    raise DomainError(422, "Attach a JPEG, PNG or WebP image.")
                if original.width * original.height > MAX_PIXELS:
                    raise DomainError(422, "The image is larger than 12 megapixels. Please resize it.")
                original.load()
                # Convert pixels, never carry EXIF/ICC/comments/filename metadata forward.
                pixels = ImageOps.exif_transpose(original).convert("RGB")
                pixels.thumbnail((2048, 2048))
                clean = Image.new("RGB", pixels.size)
                clean.paste(pixels)
                output = io.BytesIO()
                clean.save(output, format="JPEG", quality=86, optimize=True)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise DomainError(422, "The attachment could not be decoded as a supported image.") from error


def save_image(service, user, report_id, content):
    db = service.db
    with db.transaction() as connection:
        row = db.one(connection, "SELECT * FROM reports WHERE id = ? AND deleted_at IS NULL", (report_id,))
        if not row or row["user_id"] != user["id"]:
            raise DomainError(404, "Report not found.")
        if row["status"] != "pending":
            raise DomainError(409, "Images can be changed only while a report is pending review.")
        clean = clean_image(content, service.settings.upload_limit)
        filename = uuid4().hex + ".jpg"
        path = service.settings.runtime / "images" / filename
        try:
            path.write_bytes(clean)
            db.execute(connection, "UPDATE reports SET image_file = ?, image_published = 0 WHERE id = ?", (filename, report_id))
            service.audit(connection, user["id"], "image_cleaned_and_attached", report_id, {"exif_removed": True, "public": False})
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        service.delete_image(row["image_file"])
    return {"id": report_id, "has_image": True, "image_url": f"/api/reports/{report_id}/image", "public": False}
