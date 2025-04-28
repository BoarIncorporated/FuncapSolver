import base64
import ctypes
import json
import random
import time
from queue import Queue
from threading import Lock, Thread, Event
from typing import Any, Dict, List, Optional
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from threading import Lock, Thread, Event
from urllib3.util.retry import Retry
from flask import Flask, jsonify, request
import base64
import json

import orjson

import helpers
import tls_requests
from tls_requests import TLSClient

exceptions = helpers.exceptions
SetConsoleTitle = ctypes.windll.kernel32.SetConsoleTitleW
TLSClient.initialize()

_PROXIES = None
_WEBGLS = None
_DATA_LOCK = Lock()


def load_data():
    global _PROXIES, _WEBGLS
    with _DATA_LOCK:
        if _PROXIES is None:
            with open("data/proxies.txt", "r", encoding="utf-8") as file:
                _PROXIES = list(set(file.read().splitlines()))
        if _WEBGLS is None:
            with open("data/webgl.json", "rb") as file:
                _WEBGLS = orjson.loads(file.read())
    return _PROXIES, _WEBGLS

class SessionPool:
    def __init__(self, size: int = 50):
        self.pool = Queue(maxsize=size)
        self.size = size
        self.lock = Lock()
        self.retries = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )

    def get_session(
        self, preset: helpers.models.Preset, userbrowser: helpers.models.UserBrowser
    ) -> tls_requests.Client:
        try:
            return self.pool.get_nowait()
        except:
            return self._create_new_session(preset, userbrowser)

    def return_session(self, session: tls_requests.Client):
        try:
            self.pool.put_nowait(session)
        except:
            session.close()

    def _create_new_session(
        self, preset: helpers.models.Preset, userbrowser: helpers.models.UserBrowser
    ) -> tls_requests.Client:
        session = tls_requests.Client(
            client_identifier=f"okhttp4_android_{userbrowser.android_version}",
        )
        
        #proxy = random.choice(_PROXIES)
        #session.proxy = f"http://{proxy}"
        session.timeout = (5, 10)  # Connect timeout, Read timeout
        
        base_headers = helpers.constants.BASE_HEADERS
        base_headers.update({
            "User-Agent": userbrowser.user_agent,
            "sec-ch-ua": userbrowser.sec_ch_ua,
            "Host": preset.api_url.split("https://")[1],
            "Referer": preset.site_url,
            "Connection": "keep-alive",
            "Keep-Alive": "timeout=5, max=1000"
        })
        session.headers = base_headers
        return session


class Funcaptcha:
    def __init__(self, max_workers: int = 100, session_pool_size: int = 50) -> None:
        # Load data once
        load_data()

        self.session_pool = SessionPool(session_pool_size)
        self.thread_pool = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="solver"
        )
        self.blob_pool = ThreadPoolExecutor(
            max_workers=max(10, max_workers // 10),
            thread_name_prefix="blob"
        )
        self.lock = Lock()
        self.capi_version: str = ""
        self.enforcement_hash: str = ""
        self.logger = helpers.logger.Logger("Fraudster")
        self.solved, self.failed, self.instapass = 0, 0, 0
        self._shutdown = False

    def shutdown(self):
        self._shutdown = True
        self.thread_pool.shutdown(wait=True)

    def update_console_title(self, stop_event: Event):
        while not stop_event.is_set():
            instaper = (
                f"{(self.instapass / self.solved * 100):.2f}%"
                if self.solved
                else "Unknown"
            )
            SetConsoleTitle(
                f"Fraudster solver | "
                f"Solved: {self.solved} | "
                f"Instapass: {self.instapass} | "
                f"Instapass %: {instaper}"
            )
            time.sleep(0.5)

    def update_data(
        self, session: tls_requests.Client, preset: helpers.models.Preset
    ) -> None:
        r = session.get(f"{preset.api_url}/v2/{preset.site_key}/api.js")
        try:
            parts = r.text.split("/enforcement.")
            self.capi_version = parts[0].split('"')[-1]
            self.enforcement_hash = parts[1].split(".html")[0]
        except:
            self.capi_version = "2.12.0"
            self.enforcement_hash = "0a3d1c68c34cf87e8eedcc692165053d"

    def get_challenge_data(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        webgl: Dict[str, Any],
        origin_page: Optional[str] = None,
        blob: Optional[str] = None,
    ) -> helpers.models.ChallengeData:
        new_headers = helpers.constants.GET_CHALLENGE_HEADERS
        helpers.utils.update_headers(session, new_headers)
        session.headers.update(
            {
                "Referer": f"{preset.api_url}/v2/{self.capi_version}/enforcement.{self.enforcement_hash}.html",
                "Origin": preset.api_url,
                "x-ark-esync-value": helpers.arkose.short_esync(),
            }
        )

        ua = session.headers["User-Agent"]
        data = {
            "public_key": preset.site_key,
            "capi_version": self.capi_version,
            "capi_mode": preset.capi_mode,
            "style_theme": preset.style_theme,
            "rnd": str(random.random()),
            "bda": helpers.bda.get_bda(
                webgl,
                preset,
                ua,
                self.capi_version,
                self.enforcement_hash,
                session.proxy
            ),
            "site": preset.site_url,
            "userbrowser": ua,
        }
        optional_data = {
            **({"data[origin_page]": origin_page} if origin_page else {}),
            **({"data[blob]": blob} if blob else {}),
        }
        data = {**data, **optional_data}
        #print(data)
        cookies = {**session.cookies, "timestamp": session.headers["x-ark-esync-value"]}
        jsn = session.post(
            f"{preset.api_url}/fc/gt2/public_key/{preset.site_key}",
            data=data,
            cookies=cookies,
        )
        #print(jsn.text)
        jsn = jsn.json()
        if "error" in jsn:
            raise exceptions.ChallengeDataError("Failed to get challenge")
        return helpers.models.ChallengeData.from_raw_data(jsn)

    def init_load(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge_data: helpers.models.ChallengeData,
    ) -> None:
        new_headers = helpers.constants.INIT_LOAD_HEADERS
        helpers.utils.update_headers(session, new_headers)
        cookies = {**session.cookies, "timestamp": helpers.arkose.short_esync()}
        session.get(
            f"{preset.api_url}/fc/init-load/",
            params={"session_token": challenge_data.token.game_token},
            cookies=cookies,
        )

    def challenge_index(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge_data: helpers.models.ChallengeData,
    ) -> str:
        new_headers = helpers.constants.CHALLENGE_INDEX_HEADERS
        helpers.utils.update_headers(session, new_headers)

        params = {
            "session": challenge_data.token.game_token,
            "r": challenge_data.token.region,
            "lang": "en",
            "pk": preset.site_key,
            "at": challenge_data.token.at,
            "ag": challenge_data.token.ag,
            "cdn_url": challenge_data.token.cdn_url,
            "surl": challenge_data.token.surl,
            "smurl": challenge_data.token.smurl,
            "theme": "default",
        }

        return session.get(challenge_data.game_path, params=params).url  # type:ignore

    def send_analytics(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        data: Dict[str, Any],
        referer: str,
        forced_headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        new_headers = helpers.constants.ANALYTICS_HEADERS
        timestamp = helpers.arkose.x_ark_esync()
        new_headers.update(
            {
                "Referer": referer,
                "Origin": preset.site_url,
                "X-NewRelic-Timestamp": timestamp,
            }
        )
        cookies = {**session.cookies, "timestamp": timestamp}
        helpers.utils.update_headers(session, new_headers)
        headers = forced_headers if forced_headers else session.headers
        session.post(
            f"{preset.api_url}/fc/a/", data=data, cookies=cookies, headers=headers
        )

    def site_url_analytics(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge_data: helpers.models.ChallengeData,
        referer: str,
    ) -> None:
        data = {
            "sid": challenge_data.token.region,
            "session_token": challenge_data.token.game_token,
            "analytics_tier": challenge_data.token.at,
            "disableCookies": "false",
            "render_type": "canvas",
            "is_compatibility_mode": challenge_data.compatibility_mode_enabled,
            "category": "Site URL",
            "action": f"{preset.api_url}/v2/{self.capi_version}/enforcement.{self.enforcement_hash}.html",
        }
        self.send_analytics(session, preset, data, referer)

    def game_loaded_analytics(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge: helpers.models.Challenge,
        referer: str,
    ) -> None:
        data = {
            "sid": challenge.challenge_data.token.region,
            "session_token": challenge.challenge_data.token.game_token,
            "analytics_tier": challenge.challenge_data.token.at,
            "disableCookies": "false",
            "game_token": challenge.challenge_id,
            "game_type": challenge.game_type,
            "render_type": "canvas",
            "is_compatibility_mode": challenge.challenge_data.compatibility_mode_enabled,
            "category": "loaded",
            "action": "game loaded",
        }
        self.send_analytics(session, preset, data, referer)

    def clicked_verify_analytics(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge: helpers.models.Challenge,
        referer: str,
    ) -> None:
        headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Host": preset.api_url.split("https://")[1],
            "Origin": preset.api_url,
            "Referer": referer,
            "sec-ch-ua": session.headers["sec-ch-ua"],
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Android"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": session.headers["User-Agent"],
            "X-NewRelic-Timestamp": helpers.arkose.x_newrelic_timestamp(),
            "X-Requested-ID": helpers.arkose.aes_encrypt(
                json.dumps(
                    {"sc": [random.randint(100, 200), random.randint(100, 200)]}
                ).replace(" ", ""),
                f"REQUESTED{challenge.challenge_data.token.game_token}ID",
            ),
            "X-Requested-With": "XMLHttpRequest",
        }

        data = {
            "sid": challenge.challenge_data.token.region,
            "session_token": challenge.challenge_data.token.game_token,
            "analytics_tier": challenge.challenge_data.token.at,
            "disableCookies": False,
            "game_token": challenge.challenge_id,
            "game_type": challenge.game_type,
            "render_type": "canvas",
            "is_compatibility_mode": challenge.challenge_data.compatibility_mode_enabled,
            "category": "begin app",
            "action": "user clicked verify",
        }
        self.send_analytics(session, preset, data, referer, forced_headers=headers)

    def answer(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge: helpers.models.Challenge,
        referer: str,
        answers: List[str],
        dapib_code: str,
    ) -> Dict[str, Any]:
        new_headers = helpers.constants.GET_FULL_CHALLENGE_HEADERS
        timestamp = helpers.arkose.x_ark_esync()
        new_headers.update(
            {
                "Origin": preset.site_url,
                "Referer": referer,
                "X-NewRelic-Timestamp": timestamp,
            }
        )
        answers_new = str([",".join(answers)]).replace("'", "")

        result = helpers.arkose.aes_encrypt(
            answers_new, challenge.challenge_data.token.game_token
        )

        data = {
            "session_token": challenge.challenge_data.token.game_token,
            "game_token": challenge.challenge_id,
            "sid": challenge.challenge_data.token.region,
            "guess": result,
            "render_type": "canvas",
            "analytics_tier": challenge.challenge_data.token.at,
            "bio": helpers.bio.BioGenerator().generate(),
            "is_compatibility_mode": challenge.challenge_data.compatibility_mode_enabled,
        }

        if dapib_code:
            data["tguess"] = helpers.arkose.t_guess(
                session, answers, dapib_code, challenge.challenge_data.token.game_token
            )
        cookies = {**session.cookies, "timestamp": timestamp}
        response = session.post(f"{preset.api_url}/fc/ca/", data=data, cookies=cookies)
        return response.json()

    def get_challenge(
        self,
        session: tls_requests.Client,
        preset: helpers.models.Preset,
        challenge_data: helpers.models.ChallengeData,
        referer: str,
    ) -> helpers.models.Challenge:
        new_headers = helpers.constants.GET_FULL_CHALLENGE_HEADERS
        timestamp = helpers.arkose.x_ark_esync()
        new_headers.update(
            {
                "Origin": preset.site_url,
                "Referer": referer,
                "X-NewRelic-Timestamp": timestamp,
            }
        )
        cookies = {**session.cookies, "timestamp": timestamp}
        helpers.utils.update_headers(session, new_headers)
        data = {
            "token": challenge_data.token.game_token,
            "sid": challenge_data.token.region,
            "render_type": "canvas",
            "lang": "",
            "isAudioGame": "false",
            "is_compatibility_mode": challenge_data.compatibility_mode_enabled,
            "apiBreakerVersion": "green",
            "analytics_tier": challenge_data.token.at,
        }

        r = session.post(f"{preset.api_url}/fc/gfct/", data=data, cookies=cookies)
        return helpers.models.Challenge.from_raw_data(r.json(), challenge_data)

    def solve_image(self, index, img_url, challenge, session):
        response = session.get(img_url)
        if response.status_code != 200:
            raise exceptions.ImageDownloadError(f"Failed to download image: {img_url}")

        base64_img = base64.b64encode(response.content).decode("utf-8")
        index_predicted = helpers.classification.predict_image(
            base64_img, challenge, response.content
        )

        if challenge.game_type == 3:
            index_predicted += 1
            answer = json.dumps(
                helpers.utils.grid_answer_dict(index_predicted)
            ).replace(" ", "")
        else:
            answer = json.dumps({"index": index_predicted}).replace(" ", "")

        return (index, answer)

    def solve(
        self,
        preset: helpers.models.Preset,
        origin_page: Optional[str] = None,
        blob: Optional[str] = None,
        og_cookies: Optional[Dict[str, Any]] = None,
        og_proxy: Optional[str] = None,
    ) -> helpers.models.Captcha:
        if isinstance(preset, str):
            preset = helpers.presets.get_preset(preset)  # type:ignore
        if preset is None:
            raise exceptions.PresetNotFoundError(f"Couldn't find preset for {preset}")
        retries = 2
        for attempt in range(retries):
            try:
                webgl = random.choice(_WEBGLS)
                user_agent: str = webgl["user-agent"]
                android_version, chrome_version = helpers.utils.parse_user_agent(user_agent)
                userbrowser = helpers.models.UserBrowser(
                    android_version=android_version, chrome_version=chrome_version
                )

                session = self.session_pool.get_session(preset, userbrowser)
                if og_cookies:
                    session.cookies = og_cookies
                if og_proxy:
                    if og_proxy.startswith("http://"):
                        session.proxy = og_proxy
                    else:
                        session.proxy = f"http://{og_proxy}"
                try:
                    if not (self.capi_version and self.enforcement_hash):
                        with self.lock:
                            self.update_data(session, preset)

                    challenge_data = self.get_challenge_data(
                        session, preset, webgl, origin_page, blob
                    )
                    if challenge_data.token.sup1:
                        self.logger.log(
                            "white",
                            f"Token: {challenge_data.token.game_token} | Waves: 0 | Suppressed",
                        )
                        session.headers.update(
                            {
                                "Sec-Fetch-Dest": "script",
                                "Sec-Fetch-Mode": "no-cors",
                                "Sec-Fetch-Site": "same-origin",
                            }
                        )

                        self.init_load(session, preset, challenge_data)
                        session.get(
                            f"{preset.api_url}/fc/a/",
                            params={
                                "callback": f"__jsonp_{str(int(time.time() * 1000))}",
                                "category": "loaded",
                                "action": "game loaded",
                                "session_token": challenge_data.token.game_token,
                                "data[public_key]": preset.site_key,
                                "data[site]": preset.site_url,
                            },
                        )

                        self.solved += 1
                        self.instapass += 1
                        return helpers.models.Captcha(
                            solved=True,
                            token=challenge_data.token.raw,
                            waves=0,
                            variant="",
                            instapass=True,
                        )

                    referer = self.challenge_index(session, preset, challenge_data)
                    challenge = self.get_challenge(session, preset, challenge_data, referer)
                    self.logger.log("white", f"Got challenge | Waves: {challenge.waves} | Variant: {challenge.variant if challenge.variant else 'suppressed'}")
                    if challenge.waves > 15:
                        raise exceptions.TooManyWavesError(
                            f"Too many waves ({challenge.waves})"
                        )

                    self.site_url_analytics(session, preset, challenge_data, referer)
                    self.game_loaded_analytics(session, preset, challenge, referer)
                    self.clicked_verify_analytics(session, preset, challenge, referer)

                    answers = []
                    for img in challenge.images:
                        response = session.get(img)
                        if response.status_code != 200:
                            raise exceptions.ImageDownloadError(
                                f"Failed to download image: {img}"
                            )

                        base64_img = base64.b64encode(response.content).decode("utf-8")
                        index = helpers.classification.predict_image(
                            base64_img, challenge, response.content
                        )

                        if challenge.game_type == 3:
                            index += 1
                            answers.append(
                                json.dumps(helpers.utils.grid_answer_dict(index)).replace(
                                    " ", ""
                                )
                            )
                        else:
                            answers.append(json.dumps({"index": index}).replace(" ", ""))

                    if len(answers) != len(challenge.images):
                        raise exceptions.MissingAnswersError(
                            f"Answers: {len(answers)} != {len(challenge.images)} images"
                        )

                    dapib_code = ""
                    if challenge.dapib_url:
                        dapib_code = session.get(challenge.dapib_url).text

                    solved = self.answer(
                        session, preset, challenge, referer, answers, dapib_code
                    )

                    is_solved = solved.get("solved", False)
                    if is_solved:
                        self.solved += 1
                    else:
                        self.failed += 1

                    return helpers.models.Captcha(
                        solved=is_solved,
                        token=challenge.challenge_data.token.raw,
                        waves=challenge.waves,
                        variant=challenge.variant,
                        instapass=False,
                    )

                finally:
                    self.session_pool.return_session(session)

            except Exception as e:
                self.logger.log("red", f"Error solving captcha: {str(e)}")
                raise

if __name__ == "__main__":
    solver = Funcaptcha()
    stop_event = Event()
    app = Flask(__name__)

    @app.route('/solve', methods=['POST'])
    def solve_endpoint() -> tuple[dict, int]:
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
                
            private_key = data.get('private_key')
            blob = data.get('blob')
            og_cookies = data.get('og_cookies')
            og_proxy = data.get('og_proxy')

            if not private_key:
                return jsonify({'error': 'Missing required parameter: private_key'}), 400
            if not og_proxy and not data.get('niggamode'):
                return jsonify({'error': 'Missing required parameter: og_proxy'}), 400

            preset = helpers.presets.get_preset(private_key)
            if not preset:
                return jsonify({'error': f'No preset found for key: {private_key}'}), 404

            if preset.requires_blob and not blob:
                return jsonify({'error': 'Blob is required for this preset but was not provided'}), 400

            result = solver.solve(
                preset=preset,
                blob=blob,
                og_cookies=og_cookies,
                og_proxy=og_proxy
            )
            solver.logger.log(
                "white",
                f"Token: {result.token[:28]} | Waves: {result.waves} | Variant: {result.variant}",
            )

            return jsonify({
                'solved': result.solved,
                'token': result.token,
                'variant': result.variant,
                'suppressed': result.instapass
            }), 200

        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON data provided'}), 400
        except Exception as e:
            #print(traceback.format_exc())
            return jsonify({'error': 'Internal server error'}), 500

    Thread(target=lambda: app.run(host='0.0.0.0', port=5000), daemon=True).start()
    while not stop_event.is_set():
        time.sleep(1)