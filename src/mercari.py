import json
import base64
import time
import uuid
import requests
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def generate_dpop_token(url: str, method: str) -> str:
    # 1. Generate an ephemeral EC private key
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # 2. Extract public numbers for JWK format
    numbers = public_key.public_numbers()
    x_bytes = numbers.x.to_bytes(32, byteorder='big')
    y_bytes = numbers.y.to_bytes(32, byteorder='big')

    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": base64url_encode(x_bytes),
        "y": base64url_encode(y_bytes)
    }

    # 3. Create the JWT Header and Payload
    header = {
        "typ": "dpop+jwt",
        "alg": "ES256",
        "jwk": jwk
    }

    payload = {
        "iat": int(time.time()),
        "jti": str(uuid.uuid4()),
        "htu": url,
        "htm": method,
        "uuid": str(uuid.uuid4())
    }

    # 4. Serialize header & payload
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload).encode('utf-8'))
    message = f"{header_b64}.{payload_b64}"

    # 5. Sign message
    signature_der = private_key.sign(message.encode('utf-8'), ec.ECDSA(hashes.SHA256()))

    # 6. Convert DER signature to IEEE P1363 raw signature (r || s, 64 bytes)
    r, s = decode_dss_signature(signature_der)
    signature_raw = r.to_bytes(32, byteorder='big') + s.to_bytes(32, byteorder='big')
    signature_b64 = base64url_encode(signature_raw)

    return f"{message}.{signature_b64}"

async def get_item_list(keyword: str, token: str = None) -> dict | bool:
    url = "https://api.mercari.jp/v2/entities:search"
    method = "POST"
    
    # Generate fresh DPoP token for this specific request
    try:
        dpop_token = generate_dpop_token(url, method)
    except Exception as e:
        print(f"Error generating DPoP token: {e}")
        return False

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "content-type": "application/json",
        "dpop": dpop_token,
        "origin": "https://jp.mercari.com",
        "referer": "https://jp.mercari.com/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-platform": "web"
    }

    payload = {
        "searchCondition": {
            "keyword": keyword,
            "order": "ORDER_DESC",
            "sort": "SORT_CREATED_TIME",
        },
        "searchSessionId": str(uuid.uuid4()).replace("-", ""),
    }

    try:
        # Make request to search endpoint
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"Mercari API returned non-200 status code: {r.status_code} {r.reason}")
            print(r.text)
            return False
    except Exception as e:
        print(f"HTTP request error: {e}")
        return False
