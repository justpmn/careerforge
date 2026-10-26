
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError


password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    return password_hasher.hash(password)


def verify_password(
    password: str,
    stored_hash: str,
) -> bool:

    if not isinstance(password, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    if not stored_hash.startswith("$argon2id$"):
        return False

    try:
        return password_hasher.verify(
            password,
            stored_hash,
        )
    except (UnknownHashError, ValueError):
        return False
