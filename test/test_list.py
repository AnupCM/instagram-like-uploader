import base64, json, os
from moto import mock_aws
from app.aws import s3, dynamodb

os.environ["BUCKET_NAME"] = "images"
os.environ["DDB_TABLE"] = "ImageMetadata"
os.environ["AWS_REGION"] = "us-east-1"

@mock_aws
def test_list_by_user_and_tag():
    from app.handlers import upload_image, list_images

    # setup infra
    s3().create_bucket(Bucket="images")
    ddb = dynamodb()
    ddb.create_table(
        TableName="ImageMetadata",
        BillingMode="PAY_PER_REQUEST",
        AttributeDefinitions=[
            {"AttributeName":"image_id","AttributeType":"S"},
            {"AttributeName":"user_id","AttributeType":"S"},
            {"AttributeName":"created_at","AttributeType":"S"},
        ],
        KeySchema=[{"AttributeName":"image_id","KeyType":"HASH"}],
        GlobalSecondaryIndexes=[{
            "IndexName":"GSI1UserCreated",
            "KeySchema":[
                {"AttributeName":"user_id","KeyType":"HASH"},
                {"AttributeName":"created_at","KeyType":"RANGE"}
            ],
            "Projection":{"ProjectionType":"ALL"}
        }]
    )

    def up(user, tags):
        img = b"123"
        e = {
            "body": json.dumps({
                "user_id": user,
                "filename": f"{user}.png",
                "content_type":"image/png",
                "tags": tags,
                "image_b64": base64.b64encode(img).decode()
            })
        }
        return upload_image(e, None)

    up("u1", ["cats","cute"])
    up("u1", ["dogs"])
    up("u2", ["cats"])

    # list for u1 + tag=cats
    resp = list_images({"queryStringParameters":{"user_id":"u1","tag":"cats"}}, None)
    assert resp["statusCode"] == 200
    items = json.loads(resp["body"])["items"]
    assert len(items) == 1
    assert items[0]["user_id"] == "u1"
    assert "cats" in items[0]["tags"]
