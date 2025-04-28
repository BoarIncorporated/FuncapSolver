import base64
import hashlib
import json
import os
import string
import time
from typing import Any, Dict, List, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from javascript import require

from tls_client import Session

from . import models

jsdom = require("jsdom")
create_script = require("vm").Script


def x_ark_esync() -> str:
    current_time = time.time()
    timestamp_str = str(int(current_time * 1000))
    timestamp_str = timestamp_str.zfill(13)
    return f"{timestamp_str[:7]}00{timestamp_str[7:]}"


def short_esync() -> str:
    current_time = time.time()
    return str(int(current_time - (current_time % 21600)))


def x_newrelic_timestamp() -> str:
    return str(int(time.time() * 100000))


def aes_encrypt(content: str, password: str) -> str:
    salt: bytes = os.urandom(8)
    key, iv = default_evp_kdf(password.encode(), salt)

    padder = padding.PKCS7(128).padder()
    padded_data: bytes = padder.update(content.encode()) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    cipher_text: bytes = encryptor.update(padded_data) + encryptor.finalize()

    ciphertext_encoded: str = base64.b64encode(cipher_text).decode("utf-8")

    iv_hex: str = iv.hex()
    salt_hex: str = salt.hex()

    enc_data = models.EncryptionData(ciphertext_encoded, iv_hex, salt_hex)

    return json.dumps(enc_data.__dict__)


def aes_decrypt(encrypted_content: str, password: str) -> str:
    enc_data: dict = json.loads(encrypted_content)
    ciphertext: bytes = base64.b64decode(enc_data["ct"])
    iv: bytes = bytes.fromhex(enc_data["iv"])
    salt: bytes = bytes.fromhex(enc_data["s"])

    key, _ = default_evp_kdf(password.encode(), salt)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded: bytes = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data: bytes = unpadder.update(decrypted_padded) + unpadder.finalize()

    return decrypted_data.decode("utf-8")


def evp_kdf(
    password: bytes,
    salt: bytes,
    key_size: int = 32,
    iv_size: int = 16,
    iterations: int = 1,
    hash_algorithm: str = "md5",
) -> Tuple[bytes, bytes]:
    if hash_algorithm.lower() != "md5":
        raise ValueError("Unsupported hash algorithm")

    derived_key_bytes: bytes = b""
    block: bytes = b""

    while len(derived_key_bytes) < (key_size + iv_size):
        hasher = hashlib.md5()
        hasher.update(block + password + salt)
        block = hasher.digest()

        for _ in range(1, iterations):
            hasher = hashlib.md5()
            hasher.update(block)
            block = hasher.digest()

        derived_key_bytes += block

    return (
        derived_key_bytes[:key_size],
        derived_key_bytes[key_size : key_size + iv_size],
    )


def default_evp_kdf(password: bytes, salt: bytes) -> Tuple[bytes, bytes]:
    return evp_kdf(password, salt)


def is_flagged(data: List[Dict[str, Any]]) -> bool:
    if not data or not isinstance(data, list):
        return False
    values = [value for d in data for value in d.values()]
    if not values:
        return False

    def ends_with_uppercase(value):
        return value and value[-1] in string.ascii_uppercase

    return all(ends_with_uppercase(value) for value in values)


def t_guess(
    session: Session, guesses: List[str], dapib_code: str, session_token: str
) -> str:
    sess, ion = session_token.split(".")
    answers = []
    for guess in guesses:
        if "index" in str(guesses):
            answers.append(
                {
                    "index": json.loads(guess)["index"],
                    sess: ion,
                }
            )
        else:
            guess = json.loads(guess)
            answers.append(
                {
                    "px": guess["px"],
                    "py": guess["py"],
                    "x": guess["x"],
                    "y": guess["y"],
                    sess: ion,
                }
            )

    resource_loader = jsdom.ResourceLoader(
        {
            "userAgent": (
                session.headers.get("User-Agent")
                if isinstance(session.headers, dict)
                else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            )
        }
    )
    vm = jsdom.JSDOM(
        "",
        {
            "runScripts": "dangerously",
            "resources": resource_loader,
            "pretendToBeVisual": True,
            "storageQuota": 10000000,
        },
    ).getInternalVMContext()

    create_script(
        """
    response=null;

    window.parent.ae={"answer":answers}

    window.parent.ae[("dapibRecei" + "ve")]=function(data) {
    response=JSON.stringify(data);
    }
    """.replace("answers", json.dumps(answers).replace('"index"', "index"))
    ).runInContext(vm)

    create_script(dapib_code).runInContext(vm)
    result = json.loads(create_script("response").runInContext(vm))

    if is_flagged(result["tanswer"]):
        for array in result["tanswer"]:
            for item in array:
                array[item] = array[item][:-1]

    return aes_encrypt(
        json.dumps(result["tanswer"]).replace(" ", ""),
        session_token,
    )
