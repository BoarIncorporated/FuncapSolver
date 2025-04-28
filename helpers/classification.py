import time
from typing import List, Tuple, Dict, Dict, Any

from requests import post as rpost

from . import models, api_gxp

#import asyncio
#from io import BytesIO
#from PIL import Image
#import numpy as np
#import onnxruntime as ort
#import torchvision.transforms as transforms
#from pydantic import BaseModel
#from fastapi.concurrency import run_in_threadpool


MODEL_PATH = "models/3d_rollball_objects.onnx"
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
    #print('predicting using sctg')
    data= {
        "method": "base64",
        "body": img,
        "imginstructions": challenge.variant,
    }
    for _ in range(MAX_RETRIES):
        try:
            funcaptcha = API_GXP.run(data)
            solution = int(funcaptcha) - 1
            #print(f"Predicted using sctg {solution}")
            #with open(f'debug/images/{secrets.token_hex(4)}_{solution}.png', 'wb') as f:
            #    f.write(raw_image)
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
            #print('doing req to', ZIAD_SERVER)
            r = rpost(ZIAD_SERVER, json=payload)
            #print('Got results', r.text)
            result = r.json()
            #print(result)
            return int(result["result"]["best_match_index"])
        except:
            print(f"Error predicting using ziad api, retrying... {i}/{MAX_RETRIES}")
    else:
        print("Failed to predict using ziad api in max retries")




#def init_model():
#    return ort.InferenceSession(
#        MODEL_PATH,
#        providers=["CPUExecutionProvider"],
#        sess_options=ort.SessionOptions()
#    )
#
#def format_probability(prob: float) -> str:
#    return f"{prob:.14f}"
#
#
#
#transform_3d = transforms.Compose([
#    transforms.Resize((52, 52)),
#    transforms.Grayscale(num_output_channels=3),
#    transforms.ToTensor()
#])
#
#class PredictionResponse(BaseModel):
#    predicted_index: int
#    max_similarity: str
#    all_similarities: List[str]
#
#class TaskRequest(BaseModel):
#    clientKey: str
#    task: Dict[str, Any]
#
#model = init_model()
#
#
#async def predict_3d(image: Image.Image, model: ort.InferenceSession):
#    img = image.convert('RGB')
#    left_image = img.crop((0, 200, 200, 400))
#    left_image = transform_3d(left_image).numpy()
#    left_image = np.expand_dims(left_image, axis=0)
#
#    width, _ = img.size
#    total_right_images = width // 200
#    img_rights = [transform_3d(img.crop((200 * j, 0, 200 * (j + 1), 200))).numpy()
#                  for j in range(total_right_images)]
#
#    max_similarity = -1
#    most_similar_index = -1
#    all_similarities = []
#
#    for i, img_right in enumerate(img_rights):
#        img_right = np.expand_dims(img_right, axis=0)
#        outputs = await run_in_threadpool(
#            lambda: model.run(None, {
#                "input_left": left_image,
#                "input_right": img_right
#            })
#        )
#        distance = outputs[0][0][0]
#        all_similarities.append(distance)
#        if distance > max_similarity:
#            max_similarity = distance
#            most_similar_index = i
#
#    return most_similar_index, max_similarity, all_similarities

#def predict_local(img: bytes, challenge: models.Challenge, raw_image: bytes) -> str:
#    image = Image.open(BytesIO(img))
#    predicted_index, max_similarity, all_similarities = asyncio.run(predict_3d(image, model))
 #   formatted_similarities = [format_probability(p) for p in all_similarities]
 #   return str(predicted_index)

def predict_image(img: bytes, challenge: models.Challenge, raw_image: bytes, attempts: int = None) -> str:
    if not attempts:
        attempts = 0
    if challenge.variant.lower() == "3d_rollball_objects":
        ...#return predict_local(img, challenge, raw_image)
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

