import random
import re
from typing import Any, Dict, List, Tuple, Union

import orjson
from datetime import datetime, timezone
import pytz
import requests

from tls_client import Session

from . import models


def parse_user_agent(user_agent: str) -> Tuple[str, str]:
    android_match = re.search(r"Android (\d+(\.\d+)*)", user_agent)
    chrome_match = re.search(r"Chrome/(\d+)", user_agent)
    android_version = android_match.group(1) if android_match else "Unknown"
    chrome_version = chrome_match.group(1) if chrome_match else "Unknown"
    return android_version, chrome_version


def generate_userbrowser() -> models.UserBrowser:
    chrome_version = str(random.randint(130, 133))
    android_version = str(random.randint(9, 14))
    return models.UserBrowser(
        chrome_version=chrome_version, android_version=android_version
    )


def save_good_bda_data(session: Session, webgl: Dict[str, Any]):
    with open("data/good_proxies.txt", "a") as f:
        f.write(session.proxies["http"].split("//")[1] + "\n")

    try:
        with open("data/good_webgl.json", "rb") as file:
            old_good_webgls = orjson.loads(file.read())
            if not isinstance(old_good_webgls, list):
                old_good_webgls = []
    except (FileNotFoundError, orjson.JSONDecodeError):
        old_good_webgls = []

    old_good_webgls.append(webgl)

    with open("data/good_webgl.json", "wb") as file:
        file.write(orjson.dumps(old_good_webgls, option=orjson.OPT_INDENT_2))


def update_headers(session, new_headers: Dict[str, Any]) -> None:
    for key, value in new_headers.items():
        if value == "" and key in session.headers:
            new_headers[key] = session.headers[key]
    session.headers = new_headers


def hashable_webgl(fp: List[Dict[str, str]]) -> str:
    result = []

    for item in fp:
        result.append(item["key"])
        result.append(item["value"])

    return ",".join(result) + ",webgl_hash_webgl,"


def hashable_fe(fp: List[str]) -> str:
    result = []
    for item in fp:
        result.append(item.split(":")[1])
    return ";".join(result)


def get_coords(num: int) -> Tuple[float, int]:
    map = {
        1: [0, 0, 100, 100],
        2: [100, 0, 200, 100],
        3: [200, 0, 300, 100],
        4: [0, 100, 100, 200],
        5: [100, 100, 200, 200],
        6: [200, 100, 300, 200],
    }

    x1, y1, x2, y2 = map[num]
    x = (x1 + x2) / 2
    y = (y1 + y2) / 2

    if random.randint(0, 1):
        x += random.uniform(10.00001, 45.99999)
    else:
        x -= random.uniform(10.00001, 45.99999)

    if random.randint(0, 1):
        y += random.randint(0, 45)
    else:
        y -= random.randint(0, 45)

    return (float(x), int(y))


def grid_answer_dict(answer: int) -> Dict[str, Union[str, int]]:
    x, y = get_coords(answer)

    return {
        "px": str(round((x / 300), 2)),
        "py": str(round((y / 200), 2)),
        "x": x,
        "y": y,
    }

def calculate_timezone_offset(timezone_str: str) -> int:
    utc_now = datetime.now(timezone.utc)
    local_now = utc_now.astimezone(pytz.timezone(timezone_str))

    utf_offset = local_now.utcoffset()
    if not utf_offset:
        return 0

    return int((utf_offset.total_seconds() / 60) * -1)

def fetch_ip_data(proxy: str) -> models.IPData:
    response_ip_address: Dict[str, str] = requests.get(
        "https://wtfismyip.com/json",
        proxies={"http": proxy, "https": proxy},
    )
    response_json: Dict[str, str] = requests.get(
        "https://api.ipfind.com/",
        headers={
            "origin": "https://ipfind.com",
            "referer": "https://ipfind.com/",
        },
        params={"ip": response_ip_address.json()["YourFuckingIPAddress"]},
        proxies={"http": proxy, "https": proxy},
    ).json()
    time_zone: Dict[str, str] = response_json.get("timezone")
    if time_zone:
        timezone_offset: int = calculate_timezone_offset(time_zone)
    else:
        timezone_offset: int = 0

    language_code: str = response_json["languages"][0]
    main_language: str = (
        f"{language_code}-{language_code.upper()}"
        if len(language_code) == 2
        else language_code
    )

    language_list: str = ",".join([main_language, main_language.split("-")[0]])

    return models.IPData(
        timezone_offset=timezone_offset,
        language=main_language,
        languages=language_list,
    )
