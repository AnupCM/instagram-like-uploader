from typing import Any, Dict, Tuple

REQUIRED_UPLOAD_FIELDS = ["user_id", "filename", "content_type", "image_b64"]

def bad_request(message: str):
    return {"statusCode": 400, "headers": {"Content-Type": "application/json"}, "body": f'{{"error":"{message}"}}'}

def ok_json(payload: str, status: int = 200):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": payload}

def parse_json_body(event) -> Tuple[Dict[str, Any] | None, str | None]:
    import json, base64
    body = event.get("body")
    if body is None:
        return None, "Empty body"
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)
    try:
        return json.loads(body), None
    except Exception:
        return None, "Invalid JSON"
