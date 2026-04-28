import base64
import os
from io import BytesIO

from PIL import Image


def redimensionar_e_codificar(file_bytes: bytes):
    max_side = int(os.getenv("IA_MAX_IMAGEM_LADO") or "1600")
    max_side = max(1, min(max_side, 4000))

    img = Image.open(BytesIO(file_bytes))
    img = img.convert("RGB")
    resample = (
        getattr(getattr(Image, "Resampling", None), "LANCZOS", None)
        or getattr(Image, "LANCZOS", None)
        or getattr(Image, "BICUBIC", None)
    )
    img.thumbnail((max_side, max_side), resample)

    out = BytesIO()
    img.save(out, format="JPEG", quality=85, optimize=True)
    jpeg_bytes = out.getvalue()

    b64 = base64.b64encode(jpeg_bytes).decode("utf-8")
    return b64, "image/jpeg"
