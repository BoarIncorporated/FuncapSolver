from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import unquote


@dataclass
class IPData:
    timezone_offset: int
    language: str
    languages: str


@dataclass
class Timezone:
    timezone: str
    region: str
    offset: Optional[int] = field(default=0)

    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "Timezone":
        return cls(
            timezone=data["timezone"],
            region=data["regionName"],
            offset=-(data["offset"] // 60),
        )


@dataclass
class Fingerprint:
    fe: List[str]
    language: str
    user_agent: str
    webgl: Dict[str, Any]
    wh: str

    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "Fingerprint":
        return cls(
            fe=data["fe"],
            language=data["language"],
            user_agent=data["user-agent"],
            webgl=data["webgl"],
            wh=data["wh"],
        )


@dataclass
class UserBrowser:
    chrome_version: str
    android_version: str
    user_agent: Optional[str] = field(default=None)
    sec_ch_ua: Optional[str] = None

    def __post_init__(self) -> None:
        self.sec_ch_ua = f'"Not A(Brand";v="8", "Chromium";v="{self.chrome_version}", "Google Chrome";v="{self.chrome_version}"'
        self.user_agent = f"Mozilla/5.0 (Linux; Android {self.android_version}; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{self.chrome_version}.0.0.0 Safari/537.36"


@dataclass
class PresetData:
    window__ancestor_origins: List[str]
    client_config__sitedata_location_href: str
    window__tree_structure: str
    window__tree_index: List[int]


@dataclass
class Preset:
    site_url: str
    site_key: str
    api_url: str
    capi_mode: str
    style_theme: str
    requires_blob: bool
    data: PresetData

    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "Preset":
        return cls(
            site_url=data["siteurl"],
            site_key=data["sitekey"],
            api_url=data["apiurl"],
            capi_mode=data["capi_mode"],
            style_theme=data["style_theme"],
            requires_blob=data["requires_blob"],
            data=PresetData(
                window__ancestor_origins=data["data"]["window__ancestor_origins"],
                client_config__sitedata_location_href=data["data"][
                    "client_config__sitedata_location_href"
                ],
                window__tree_structure=data["data"]["window__tree_structure"],
                window__tree_index=data["data"]["window__tree_index"],
            ),
        )


@dataclass
class EncryptionData:
    ct: str
    iv: str
    s: str


@dataclass
class Token:
    game_token: str
    region: str
    meta: int
    meta_width: int
    meta_height: int
    meta_bg_color: str
    meta_icon_color: str
    gui_text_color: str
    at: int
    ag: int
    cdn_url: str
    surl: str
    smurl: str
    sup1: bool
    raw: str

    @classmethod
    def from_raw_data(cls, token: str) -> "Token":
        token_parts = token.split("|")
        token_dict = {}

        for part in token_parts[1:]:
            key, value = part.split("=")
            token_dict[key] = unquote(value)

        def get_int(key: str, default: int = 0) -> int:
            return int(token_dict.get(key, default))

        def get_str(key: str, default: str = "") -> str:
            return token_dict.get(key, default)

        return cls(
            game_token=token_parts[0],
            region=get_str("r"),
            meta=get_int("meta"),
            meta_width=get_int("meta_width"),
            meta_height=get_int("meta_height"),
            meta_bg_color=get_str("metabgclr"),
            meta_icon_color=get_str("metaiconclr"),
            gui_text_color=get_str("guitextcolor"),
            at=get_int("at"),
            ag=get_int("ag"),
            cdn_url=get_str("cdn_url"),
            surl=get_str("surl"),
            smurl=get_str("smurl"),
            sup1="sup=1|" in token,
            raw=token,
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.game_token}) | {self.region}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.game_token}) | {self.region}"


@dataclass
class ChallengeData:
    token: Token
    mbio: bool
    tbio: bool
    kbio: bool
    compatibility_mode_enabled: bool
    pow: bool
    game_path: str

    @classmethod
    def from_raw_data(cls, data: Dict[str, Any]) -> "ChallengeData":
        version = data["challenge_url_cdn"].split("bootstrap/")[1].split("/")[0]
        game_path = f"https://client-api.arkoselabs.com/fc/assets/ec-game-core/game-core/{version}/standard/index.html"
        return cls(
            token=Token.from_raw_data(data["token"]),
            mbio=data["mbio"],
            tbio=data["tbio"],
            kbio=data["kbio"],
            compatibility_mode_enabled=data["compatibility_mode_enabled"],
            pow=data["pow"],
            game_path=game_path,
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(token={self.token}, compatibility mode: {self.compatibility_mode_enabled}, pow: {self.pow})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(token={self.token}, compatibility mode: {self.compatibility_mode_enabled}, pow: {self.pow})"


@dataclass
class Challenge:
    challenge_data: ChallengeData
    region: str
    challenge_id: str
    images: List[str]
    encryption_enabled: bool
    waves: int
    game_type: int
    game_difficulty: int
    variant: str
    dapib_url: Optional[str] = None

    @classmethod
    def from_raw_data(
        cls, data: Dict[str, Any], challenge_data: ChallengeData
    ) -> "Challenge":
        return cls(
            challenge_data=challenge_data,
            region=data["sid"],
            challenge_id=data["challengeID"],
            images=data["game_data"]["customGUI"]["_challenge_imgs"],
            encryption_enabled=data["game_data"]["customGUI"].get("encrypted_mode"),
            waves=data["game_data"]["waves"],
            game_type=data["game_data"]["gameType"],
            game_difficulty=data["game_data"].get("game_difficulty"),
            variant=data["game_data"].get("instruction_string", data["game_data"].get("game_variant")),
            dapib_url=data.get("dapib_url"),
        )

    def __str__(self) -> str:
        return f"Token: {self.challenge_data.token.game_token} | Waves: {self.waves} | Type: {self.variant} | Difficulty: {self.game_difficulty}"

    def __repr__(self) -> str:
        return f"Token: {self.challenge_data.token.game_token} | Waves: {self.waves} | Type: {self.variant} | Difficulty: {self.game_difficulty}"


@dataclass
class Captcha:
    solved: bool
    token: str
    waves: int
    variant: str
    instapass: bool

    def __str__(self) -> str:
        return f"Solved: {self.solved} | Token: {self.token[:28]} | Waves: {self.waves} | Variant: {self.variant if self.variant else 'Suppressed'}"

    def __repr__(self) -> str:
        return f"Solved: {self.solved} | Token: {self.token[:28]} | Waves: {self.waves} | Variant: {self.variant if self.variant else 'Suppressed'}"
