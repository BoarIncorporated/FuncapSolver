# FunCaptcha Solver API

This API provides a service to solve FunCaptcha challenges. It handles the entire process of solving FunCaptcha challenges, including browser fingerprinting, challenge solving, and token generation.

## API Endpoint

### Solve FunCaptcha

**Endpoint:** `http://127.0.0.1:5000/solve`

**Method:** POST

**Content-Type:** application/json

#### Request Body

```json
{
    "private_key": "string",     // Required: The FunCaptcha site key
    "og_proxy": "string",        // Required: Proxy URL with http:// prefix
    "blob": "string",           // Required if sitekey requires it: Additional blob data
    "og_cookies": "string"      // Optional: Required for Roblox, dictionary of cookies
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

## Notes

- The API requires a valid proxy URL with the `http://` prefix
- For Roblox captchas, `og_cookies` is required
- The `blob` parameter is only required for certain site keys that specifically need it
- You will have to add your own fingerprints
