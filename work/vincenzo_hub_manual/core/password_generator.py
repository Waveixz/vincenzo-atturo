from __future__ import annotations

import hashlib
import os
import secrets
import string
from pathlib import Path

from argon2.low_level import Type as Argon2Type
from argon2.low_level import hash_secret_raw


MIN_LEN = 12
MAX_LEN = 64
RAW_LEN = 32
CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789!@#$%^&*-_=+"
UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGIT = string.digits
SYMBOL = "!@#$%^&*-_=+"
PEPPER_FILE = Path(__file__).resolve().parents[1] / "data" / "password_pepper.bin"


def clamp(number: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, number))


def load_pepper() -> bytes:
    configured = os.getenv("VA_PASSWORD_PEPPER") or os.getenv("DERIVE_PEPPER")
    if configured:
        return configured.encode("utf-8")
    if PEPPER_FILE.exists():
        return PEPPER_FILE.read_bytes()
    PEPPER_FILE.parent.mkdir(parents=True, exist_ok=True)
    pepper = secrets.token_bytes(32)
    try:
        with PEPPER_FILE.open("xb") as handle:
            handle.write(pepper)
    except FileExistsError:
        return PEPPER_FILE.read_bytes()
    return pepper


def salt16(service: str, pepper: bytes) -> bytes:
    message = service.strip().encode("utf-8") + b"|" + pepper
    return hashlib.sha256(message).digest()[:16]


def derive_raw(master: str, service: str, pepper: bytes) -> bytes:
    return hash_secret_raw(
        secret=master.encode("utf-8"),
        salt=salt16(service, pepper),
        time_cost=3,
        memory_cost=65536,
        parallelism=1,
        hash_len=RAW_LEN,
        type=Argon2Type.ID,
    )


def raw_to_password(raw: bytes, length: int) -> str:
    length = clamp(int(length), MIN_LEN, MAX_LEN)
    output = []
    for byte in raw:
        output.append(CHARSET[byte % len(CHARSET)])
        if len(output) >= length:
            break
    current = raw
    while len(output) < length:
        current = hashlib.sha256(current).digest()
        for byte in current:
            output.append(CHARSET[byte % len(CHARSET)])
            if len(output) >= length:
                break
    return "".join(output)


def enforce_policy(password: str, raw: bytes) -> str:
    output = list(password)
    categories = (
        (UPPER, UPPER),
        (LOWER, LOWER),
        (DIGIT, DIGIT),
        (SYMBOL, SYMBOL),
    )
    missing = [alphabet for members, alphabet in categories if not any(char in members for char in password)]
    used_positions = set()
    raw_index = 0
    for alphabet in missing:
        position = raw[raw_index] % len(output)
        while position in used_positions:
            raw_index += 1
            position = raw[raw_index % len(raw)] % len(output)
        used_positions.add(position)
        raw_index += 1
        output[position] = alphabet[raw[raw_index % len(raw)] % len(alphabet)]
        raw_index += 1
    return "".join(output)


def derive_password(master: str, service: str, length: int, pepper: bytes | None = None) -> str:
    if not master.strip():
        raise ValueError("Inserisci la chiave principale.")
    if not service.strip():
        raise ValueError("Inserisci il servizio.")
    raw = derive_raw(master, service, pepper or load_pepper())
    return enforce_policy(raw_to_password(raw, length), raw)
