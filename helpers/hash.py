import hashlib
import struct
from typing import Union

import mmh3


def md5hash(content: Union[str, bytes]) -> str:
    if isinstance(content, bytes):
        return hashlib.md5(content).hexdigest()
    return hashlib.md5(content.encode()).hexdigest()


def x64hash128(content: Union[str, bytes], seed: int = 0) -> str:
    if isinstance(content, str):
        content = content.encode()
    hash_bytes: bytes = mmh3.hash_bytes(content, seed=seed, x64arch=True)
    hash_parts: tuple[int, int] = struct.unpack("<QQ", hash_bytes)
    hash_hex_str: str = "{:016x}{:016x}".format(*hash_parts)

    return hash_hex_str
