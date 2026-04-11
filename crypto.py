"""
Token encryption module — AES-128 Fernet encryption (cryptography library).
Tokens are encrypted before being stored in the database.
Even if the database is fully compromised, tokens cannot be recovered without TOKEN_ENCRYPTION_KEY.
"""

import os
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Return a cached Fernet instance, initialising it from env on first call."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = os.environ.get("TOKEN_ENCRYPTION_KEY", "").strip()
    if not key:
        # Auto-generate a key at runtime (survives the process but not restarts).
        # Warn loudly — without a persistent key, stored tokens can't be decrypted
        # after a restart.  Set TOKEN_ENCRYPTION_KEY in Replit Secrets to fix this.
        logger.warning(
            "TOKEN_ENCRYPTION_KEY not set! Generating a temporary key. "
            "Set TOKEN_ENCRYPTION_KEY in Secrets so tokens survive restarts."
        )
        key = Fernet.generate_key().decode()
        os.environ["TOKEN_ENCRYPTION_KEY"] = key  # cache for this process lifetime

    try:
        _fernet = Fernet(key.encode())
    except Exception as e:
        logger.error(f"Invalid TOKEN_ENCRYPTION_KEY: {e}. Generating a temporary key.")
        key = Fernet.generate_key().decode()
        os.environ["TOKEN_ENCRYPTION_KEY"] = key
        _fernet = Fernet(key.encode())

    return _fernet


def encrypt_token(plain_token: str) -> str:
    """Encrypt a Discord token. Returns a URL-safe base64 ciphertext string."""
    return _get_fernet().encrypt(plain_token.encode()).decode()


def decrypt_token(cipher_token: str) -> str:
    """Decrypt an encrypted token back to plaintext. Raises ValueError on failure."""
    try:
        return _get_fernet().decrypt(cipher_token.encode()).decode()
    except InvalidToken:
        raise ValueError("Token decryption failed — invalid ciphertext or wrong key.")


def is_encrypted(value: str) -> bool:
    """
    Heuristic: Fernet tokens start with 'gAAAAA' and are longer than 80 chars.
    Used to detect plaintext legacy tokens in the database.
    """
    return value.startswith("gAAAAA") and len(value) > 80
