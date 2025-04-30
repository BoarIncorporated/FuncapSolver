import time
from typing import List, Tuple, Dict

from requests import post as rpost

from . import models, api_gxp

xevil_nodes: List[Tuple[str, str]] = [
    ("http://127.0.0.1:80", "3c91bbcbe20b70107607e83e0fc83e35"),
]
api_url_create: str = "/in.php"
api_url_get: str = "/res.php"

ZIAD_SERVER = "https://api.fcap.fun/match_image"
ZIAD_API_KEY = "no"

SOLVER_CAPTCHA_TG_API_KEY = "no"
API_GXP = api_gxp.Api_GXP()
API_GXP.key = SOLVER_CAPTCHA_TG_API_KEY

MAX_RETRIES = 3

def sctg_predict(img: bytes, challenge: models.Challenge, raw_image: bytes) -> str:
    data= {
        "method": "base64",
        "body": img,
        "imginstructions": challenge.variant,
    }
    for _ in range(MAX_RETRIES):
        try:
            funcaptcha = API_GXP.run(data)
            solution = int(funcaptcha) - 1
            return solution
        except:
            print(f"Failed to predict using sctg {_}/{MAX_RETRIES}")
    else:
        print(f"Failed to predict using sctg in max retries ({MAX_RETRIES}), resorting to ziad api")
        return ziad_predict(img, challenge, raw_image)

def ziad_predict(img: bytes, challenge: models.Challenge, raw_image: bytes) -> str:
    print('backup predicting')
    payload = {
        "image": img,
        "variant": challenge.variant,
        "key": ZIAD_API_KEY
    }

    for i in range(MAX_RETRIES):
        try:
            r = rpost(ZIAD_SERVER, json=payload)
            result = r.json()
            return int(result["result"]["best_match_index"])
        except:
            print(f"Error predicting using ziad api, retrying... {i}/{MAX_RETRIES}")
    else:
        print("Failed to predict using ziad api in max retries")




def predict_image(img: bytes, challenge: models.Challenge, raw_image: bytes, attempts: int = None) -> str:
    if not attempts:
        attempts = 0
    if attempts >= MAX_RETRIES or challenge.variant.lower() in ["watericoncup", "pathfinder"]:
        return sctg_predict(img, challenge, raw_image)
    #print('predicting')
    for api_url, api_key in xevil_nodes:
        payload: Dict[str, str] = {
            "key": api_key,
            "recaptcha": "1",
            "method": "base64",
            "body": img,
            "imginstructions": challenge.variant,
        }

        try:
            response = rpost(
                f"{api_url}{api_url_create}", data=payload
            )
            
            response_content: str = response.text
            if not response_content.startswith("OK"):
                continue

            task_id: str = response_content.split("|")[1]
            status_payload: Dict[str, str] = {
                "key": api_key,
                "action": "get",
                "id": task_id,
            }
            while True:
                solution_response = rpost(
                    f"{api_url}{api_url_get}", data=status_payload
                )
                solution_content = solution_response.text
                
                if solution_content.startswith("OK"):
                    result = int(solution_content.split("|")[1]) - 1
                    return result
        
                elif solution_content == "ERROR_CAPTCHA_UNSOLVABLE":
                    break

                time.sleep(1)

        except Exception:
            return predict_image(img, challenge, raw_image, attempts+1)

