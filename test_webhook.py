import base64
import hashlib
import hmac
import json

import httpx


SECRET = "test_secret_123"

payload = {
    "id": 123456789,
    "name": "#1001",
    "email": "customer@example.com",
    "shipping_address": {
        "address1": "12 Some Street",
        "address2": "Valecherry",
        "city": "Chennai",
        "province": "Tamil Nadu",
        "country": "India",
        "country_code": "IN",
        "zip": "600053",
    },
}

raw_body = json.dumps(payload).encode("utf-8")

digest = hmac.new(
    SECRET.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).digest()

signature = base64.b64encode(digest).decode("utf-8")

response = httpx.post(
    "http://localhost:8000/webhooks/shopify/orders/create",
    content=raw_body,
    headers={
        "Content-Type": "application/json",
        "X-Shopify-Hmac-SHA256": signature,
    },
)

print(response.status_code)
print(response.text)