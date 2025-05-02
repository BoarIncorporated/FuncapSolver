from typing import Optional

from . import models

PRESETS = {
    # ROBLOX REG
    "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F": {
        "siteurl": "https://www.roblox.com",
        "sitekey": "A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F",
        "apiurl": "https://arkoselabs.roblox.com",
        "capi_mode": "inline",
        "style_theme": "default",
        "requires_blob": True,
        "data": {
            "window__ancestor_origins": [
                "https://www.roblox.com",
                "https://www.roblox.com",
            ],
            "client_config__sitedata_location_href": "https://www.roblox.com/arkose/iframe",
            "window__tree_structure": "[[[]]]",
            "window__tree_index": [0, 0],
        },
    },
    # X WEB REG
    "2CB16598-CB82-4CF7-B332-5990DB66F3AB": {
        "siteurl": "https://iframe.arkoselabs.com",
        "sitekey": "2CB16598-CB82-4CF7-B332-5990DB66F3AB",
        "apiurl": "https://client-api.arkoselabs.com",
        "capi_mode": "inline",
        "style_theme": "dark",
        "requires_blob": True,
        "data": {
            "window__ancestor_origins": [
                "https://iframe.arkoselabs.com",
                "https://x.com"
            ],
            "client_config__sitedata_location_href": "https://iframe.arkoselabs.com/2CB16598-CB82-4CF7-B332-5990DB66F3AB/index.html",
            "window__tree_structure": "[[[]]]",
            "window__tree_index": [0, 0],
        },
    },
    # OUTLOOK MOBILE REG
    "B7D8911C-5CC8-A9A3-35B0-554ACEE604DA": {
        "siteurl": "https://iframe.arkoselabs.com",
        "sitekey": "B7D8911C-5CC8-A9A3-35B0-554ACEE604DA",
        "apiurl": "https://client-api.arkoselabs.com",
        "capi_mode": "inline",
        "style_theme": "sisu_light",
        "requires_blob": True,
        "data": {
            "window__ancestor_origins": [
                "https://iframe.arkoselabs.com",
                "https://signup.live.com"
            ],
            "client_config__sitedata_location_href": "https://iframe.arkoselabs.com/B7D8911C-5CC8-A9A3-35B0-554ACEE604DA/index.html",
            "window__tree_structure": "[[[]],[],[[]]]",
            "window__tree_index": [2, 0],
        },
    },
    # ZILCH SIGN UP
    "D5264E07-85CF-434C-88E5-6F095A832C01": {
        "siteurl": "https://customers.payzilch.com",
        "sitekey": "D5264E07-85CF-434C-88E5-6F095A832C01",
        "apiurl": "https://client-api.arkoselabs.com",
        "capi_mode": "lightbox",
        "style_theme": "default",
        "requires_blob": True,
        "data": {
            "window__ancestor_origins": [
                "https://customers.payzilch.com"
            ],
            "client_config__sitedata_location_href": "https://customers.payzilch.com/apply/",
            "window__tree_structure": "[[],[],[],[]]",
            "window__tree_index": [3],
        },
    },
    # ZILCH LOGIN
    "284CE8B2-89E0-45B0-98B7-38594A810745": {
        "siteurl": "https://customers.payzilch.com",
        "sitekey": "284CE8B2-89E0-45B0-98B7-38594A810745",
        "apiurl": "https://client-api.arkoselabs.com",
        "capi_mode": "lightbox",
        "style_theme": "default",
        "requires_blob": True,
        "data": {
            "window__ancestor_origins": [
                "https://customers.payzilch.com"
            ],
            "client_config__sitedata_location_href": "https://customers.payzilch.com/login",
            "window__tree_structure": "[[],[]]",
            "window__tree_index": [1],
        },
    },
}


def get_preset(sitekey: str) -> Optional[models.Preset]:
    if sitekey not in PRESETS:
        return None
    return models.Preset.from_raw_data(PRESETS[sitekey])
