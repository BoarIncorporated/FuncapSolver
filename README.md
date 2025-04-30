# FunCaptcha Solver API

This code provides an API for retrieving funcaptcha tokens and contains all the necessary functions to fetch them and solve them, it's able to produce unflagged tokens (idk for how long but it is)

Original author is https://t.me/Dinglenut18, you can contact me at any time for paid code commissions but not for help with this repo please, if you need help open an Issue and hope someone helps you or read the setup

## API Endpoint

### Solve FunCaptcha

**Endpoint:** `http://127.0.0.1:5000/solve`

**Method:** POST

**Content-Type:** `application/json`

#### Request Body

```json
{
    "private_key": str,     // Required: The FunCaptcha site key
    "og_proxy": str,        // Required: Proxy URL with http:// prefix
    "blob": str,           // Required if sitekey requires it: Additional blob data
    "og_cookies": Dict[str, str],      // Optional: Required for Roblox, dictionary of cookies
    "niggamode": bool // Optional: If set to true it will allow for proxyless task
}
```

#### Response

```json
{
    "solved": boolean,          // Whether the captcha was successfully solved
    "token": string,           // The generated token if solved
    "variant": string,         // The variant of the captcha
    "suppressed": boolean      // Whether the response was suppressed
}
```

#### Example Request

```python
import requests
import json

session = requests.Session()

url = "http://127.0.0.1:5000/solve"
payload = {
    "private_key": "YOUR_SITE_KEY",
    "og_proxy": "http://username:password@ip:port",
    "blob": "optional-blob-data",
    "og_cookies": session.cookies.get_dict()
}

response = requests.post(url, json=payload)
result = response.json()
```

#### Example Response

```json
{
    "solved": true,
    "token": "...",
    "variant": "pathfinder",
    "suppressed": false
}
```

## Error Handling

The API will return appropriate HTTP status codes:

- 200: Successful request
- 400: Invalid request parameters
- 500: Internal server error

## Setup
- Add proxies to `data/proxies.txt` (maybe optional? I forgot)
- Ideally add more fingerprints to `data/webgl.json`
- Change xevil node [here](https://github.com/BoarIncorporated/FuncapSolver/blob/9f6c073395ea72c5de16a4b68ef139a15181aaa9/helpers/classification.py#L20) or add Ziad api key [here](https://github.com/BoarIncorporated/FuncapSolver/blob/9f6c073395ea72c5de16a4b68ef139a15181aaa9/helpers/classification.py#L26) or [SCTG](https://t.me/Xevil_check_bot) key [here](https://github.com/BoarIncorporated/FuncapSolver/blob/9f6c073395ea72c5de16a4b68ef139a15181aaa9/helpers/classification.py#L28)
- Ideally use your own tls_client config (I did not include mine here it's using default)
- Run `pip install -r requirements.txt`
- Run `python app.py`
- I think you also need to install nodejs from [here](https://nodejs.org/en/download)
- Anything else either figure out yourself or ask gptchatDeepsekAI

## Notes

- The API requires a valid proxy URL with the `http://` prefix
- For Roblox captchas, `og_cookies` is required
- The `blob` parameter is only required for certain site keys that specifically need it
- You will have to add your own fingerprints
- Unlike the other solver repos I have this one still currently works and tokens pass
- If you encounter an error and you don't know why, either [enable traceback](https://github.com/BoarIncorporated/FuncapSolver/blob/1f9f399d1b8ec585a9282dafd3fecf85e5a1dcba/app.py#L638) or make sure your preset is in the `helpers/presets.py` file

## Credits
- [@trailios](https://github.com/trailios/) for the encryption/decryption algos and x64hash128 ready-to-use code
- [@uizlrfwg](https://github.com/uizlrfwg/) for the local prediction source, you can find the download link for the model in [his repo](https://github.com/uizlrfwg/fun-process_image)
