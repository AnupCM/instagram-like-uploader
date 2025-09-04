import os, json, base64, hashlib, uuid, datetime
from .aws import s3
from .models import put_metadata, get_metadata, delete_metadata, query_by_user_id, scan_by_tag
from .validation import parse_json_body, bad_request, ok_json

BUCKET = os.getenv("BUCKET_NAME", "images")
DEFAULT_LIMIT = int(os.getenv("LIST_LIMIT", "50"))

def _now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def upload_image(event, context):
    """
    POST /images
    Body: {
      "user_id": "u123",
      "filename": "cat.png",
      "content_type": "image/png",
      "tags": ["cats","cute"],
      "image_b64": "<base64-encoded-bytes>"
    }
    """
    body, err = parse_json_body(event)
    if err:
        return bad_request(err)

    for f in ("user_id","filename","content_type","image_b64"):
        if f not in body:
            return bad_request(f"Missing field: {f}")

    try:
        binary = base64.b64decode(body["image_b64"])
    except Exception:
        return bad_request("image_b64 is not valid base64")

    image_id = str(uuid.uuid4())
    user_id = body["user_id"]
    filename = body["filename"]
    content_type = body["content_type"]
    tags = body.get("tags", [])

    s3_key = f"{user_id}/{image_id}/{filename}"
    sha256 = hashlib.sha256(binary).hexdigest()

    s3().put_object(
        Bucket=BUCKET, Key=s3_key, Body=binary, ContentType=content_type, Metadata={
            "image_id": image_id, "user_id": user_id, "filename": filename, "checksum_sha256": sha256
        }
    )

    item = {
        "image_id": image_id,
        "user_id": user_id,
        "filename": filename,
        "content_type": content_type,
        "size": len(binary),
        "tags": tags,
        "created_at": _now_iso(),
        "s3_bucket": BUCKET,
        "s3_key": s3_key,
        "checksum_sha256": sha256
    }
    put_metadata(item)
    return ok_json(json.dumps({"image_id": image_id, "s3_key": s3_key}), 201)

def list_images(event, context):
    """
    GET /images?user_id=...&tag=...&created_after=...&created_before=...&limit=...
    Supports filters: user_id, tag; optional time window.
    """
    params = event.get("queryStringParameters") or {}
    limit = int(params.get("limit", DEFAULT_LIMIT))

    user_id = params.get("user_id")
    tag = params.get("tag")
    created_after = params.get("created_after")
    created_before = params.get("created_before")

    items = []
    if user_id:
        items = query_by_user_id(user_id=user_id, limit=limit, created_after=created_after, created_before=created_before)
        if tag:
            # apply tag filter on the results
            items = [i for i in items if tag in (i.get("tags") or [])]
    elif tag:
        items = scan_by_tag(tag=tag, limit=limit)
    else:
        # minimal fallback; in production prefer a "recent-images" GSI or require at least one filter
        from .aws import dynamodb
        table = dynamodb().Table(os.getenv("DDB_TABLE", "ImageMetadata"))
        items = table.scan(Limit=limit).get("Items", [])

    return ok_json(json.dumps({"items": items}))

def get_image(event, context):
    """
    GET /images/{image_id}?download=true|false
    Returns presigned URL (view) or download.
    """
    image_id = event["pathParameters"]["image_id"]
    download = (event.get("queryStringParameters") or {}).get("download", "false").lower() == "true"
    item = get_metadata(image_id)
    if not item:
        return {"statusCode": 404, "body": '{"error":"Not found"}'}

    params = {"Bucket": item["s3_bucket"], "Key": item["s3_key"]}
    if download:
        params["ResponseContentDisposition"] = f'attachment; filename="{item["filename"]}"'
    url = s3().generate_presigned_url("get_object", Params=params, ExpiresIn=900)

    return ok_json(json.dumps({"url": url, "content_type": item["content_type"], "filename": item["filename"]}))

def delete_image(event, context):
    """
    DELETE /images/{image_id}
    """
    image_id = event["pathParameters"]["image_id"]
    item = get_metadata(image_id)
    if not item:
        return {"statusCode": 404, "body": '{"error":"Not found"}'}

    s3().delete_object(Bucket=item["s3_bucket"], Key=item["s3_key"])
    delete_metadata(image_id)
    return {"statusCode": 204, "body": ""}
