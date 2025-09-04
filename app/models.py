import os
from .aws import dynamodb

DDB = dynamodb()
TABLE_NAME = os.getenv("DDB_TABLE", "ImageMetadata")
TABLE = DDB.Table(TABLE_NAME)

# Item shape:
# {
#   "image_id": str (PK),
#   "user_id": str,
#   "filename": str,
#   "content_type": str,
#   "size": int,
#   "tags": list[str],
#   "created_at": str (ISO8601),
#   "s3_bucket": str,
#   "s3_key": str,
#   "checksum_sha256": str
# }

def put_metadata(item: dict):
    TABLE.put_item(Item=item)

def get_metadata(image_id: str):
    resp = TABLE.get_item(Key={"image_id": image_id})
    return resp.get("Item")

def delete_metadata(image_id: str):
    TABLE.delete_item(Key={"image_id": image_id})

def query_by_user_id(user_id: str, limit: int = 50, created_after: str | None = None, created_before: str | None = None):
    # GSI1: user_id-created_at (PK user_id, SK created_at)
    from boto3.dynamodb.conditions import Key, Attr
    kwargs = {
        "IndexName": "GSI1UserCreated",
        "KeyConditionExpression": Key("user_id").eq(user_id),
        "Limit": limit
    }
    if created_after or created_before:
        # add range filter on created_at
        cond = []
        if created_after:
            cond.append(Key("created_at").gte(created_after))
        if created_before:
            cond.append(Key("created_at").lte(created_before))
        # chain conditions
        if len(cond) == 2:
            kwargs["KeyConditionExpression"] = Key("user_id").eq(user_id) & cond[0] & cond[1]
        else:
            kwargs["KeyConditionExpression"] = Key("user_id").eq(user_id) & cond[0]
    return TABLE.query(**kwargs)["Items"]

def scan_by_tag(tag: str, limit: int = 50):
    # GSI2: tag-index with "tag" as PK (store exploded tags for secondary index)
    # Simpler approach here: filter-expression scan (works locally; GSI recommended for prod)
    from boto3.dynamodb.conditions import Attr
    resp = TABLE.scan(
        FilterExpression=Attr("tags").contains(tag),
        Limit=limit
    )
    return resp.get("Items", [])
