import hashlib
import json
import random
from typing import Tuple

ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def ripemd160(data: bytes) -> bytes:
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.digest()


def double_sha256(data: bytes) -> bytes:
    return sha256(sha256(data))


def b58encode(data: bytes) -> str:
    num = int.from_bytes(data, "big")
    enc = ""
    while num > 0:
        num, rem = divmod(num, 58)
        enc = ALPHABET[rem] + enc
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return "1" * pad + (enc or "1")


def b58check_encode(version: bytes, payload: bytes) -> str:
    raw = version + payload
    checksum = double_sha256(raw)[:4]
    return b58encode(raw + checksum)


def seed_to_private_bytes(seed: str) -> bytes:
    return sha256(seed.encode("utf-8"))


def wif_from_seed(seed: str, compressed: bool = True) -> str:
    key32 = seed_to_private_bytes(seed)
    suffix = b"\x01" if compressed else b""
    return b58check_encode(b"\x80", key32 + suffix)


def compressed_pubkey_from_seed(seed: str) -> str:
    key32 = seed_to_private_bytes(seed)
    x = sha256(b"pub-x" + key32)
    prefix = b"\x02" if (x[-1] % 2 == 0) else b"\x03"
    return (prefix + x).hex()


def btc_address_from_pubkey_hex(pubkey_hex: str) -> str:
    pub = bytes.fromhex(pubkey_hex)
    h160 = ripemd160(sha256(pub))
    return b58check_encode(b"\x00", h160)


def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def is_probable_prime(n: int, k: int = 8) -> bool:
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23):
        if n % p == 0:
            return n == p
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def deterministic_prime(seed: bytes, salt: bytes) -> int:
    x = int.from_bytes(sha256(seed + salt), "big") | 1
    x |= (1 << 255)
    while not is_probable_prime(x):
        x += 2
    return x


def private_key_from_seed(seed: str) -> Tuple[int, int, int]:
    seed_b = seed.encode()
    p = deterministic_prime(seed_b, b"p")
    q = deterministic_prime(seed_b, b"q")
    if p == q:
        q = deterministic_prime(seed_b, b"q2")
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537
    d = modinv(e, phi)
    return n, e, d


def address_from_public_key(n: int, e: int) -> str:
    pub = f"{n}:{e}".encode()
    payload = b"\x00" + sha256(pub)[:20]
    checksum = double_sha256(payload)[:4]
    return b58encode(payload + checksum)


def sign_message(n: int, d: int, message: bytes) -> str:
    h = int.from_bytes(sha256(message), "big")
    sig = pow(h, d, n)
    return hex(sig)[2:]


def verify_message(n: int, e: int, message: bytes, signature_hex: str) -> bool:
    try:
        sig = int(signature_hex, 16)
    except ValueError:
        return False
    h = int.from_bytes(sha256(message), "big")
    return pow(sig, e, n) == h % n


def keypair_from_seed(seed: str) -> Tuple[Tuple[int, int, int], str, str]:
    n, e, d = private_key_from_seed(seed)
    pub = json.dumps({"n": str(n), "e": e})
    return (n, e, d), pub, address_from_public_key(n, e)
