import os
from functools import lru_cache
import base64
import binascii
import string

import anthropic
from cryptography.fernet import Fernet, InvalidToken
from cryptography.fernet import Fernet as _FernetType


@lru_cache(maxsize=1)
def _get_fernet() -> _FernetType | None:
    key = os.getenv("IA_MASTER_KEY")
    if not key:
        return None
    key = str(key).strip()
    if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
        key = key[1:-1].strip()
    allowed = set(string.ascii_letters + string.digits + "-_=")
    if not key or any((ch not in allowed) for ch in key):
        raise ValueError("IA_MASTER_KEY inválida: contém caracteres inválidos.")
    try:
        raw = base64.urlsafe_b64decode(key.encode("utf-8"))
        if len(raw) != 32:
            raise ValueError("IA_MASTER_KEY inválida: precisa decodificar para 32 bytes.")
        return Fernet(key.encode("utf-8"))
    except (binascii.Error, ValueError):
        raise
    except Exception:
        raise ValueError("IA_MASTER_KEY inválida: formato incompatível com Fernet.")


def encrypt_secret(raw: str) -> str:
    f = _get_fernet()
    if f is None:
        raise ValueError("IA_MASTER_KEY ausente")
    token = f.encrypt(raw.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_secret(token: str) -> str:
    f = _get_fernet()
    if f is None:
        raise ValueError("IA_MASTER_KEY ausente")
    try:
        raw = f.decrypt(token.encode("utf-8"))
    except InvalidToken:
        raise ValueError("Segredo inválido")
    return raw.decode("utf-8")


def mask_secret(raw: str) -> str:
    s = str(raw or "")
    if len(s) <= 4:
        return "****"
    return f"****{s[-4:]}"


def get_client(api_key: str | None = None):
    key = api_key or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        return anthropic.Anthropic(api_key=key, timeout=30.0)
    except TypeError:
        return anthropic.Anthropic(api_key=key)
