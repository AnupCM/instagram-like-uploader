import base64, json, os
from moto import mock_aws
import boto3

os.environ["BUCKET_NAME"] = "images"
os.environ["DDB_TABLE"] = "ImageMetadata"
os.environ["AWS_REGION"] = "us-east-1"

@mock_aws
def test_upload_image():
    from app.handlers import upload_image
    from app.aws import s3, dynamodb

    # create infra in moto
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

    img = b"\x89PNG...."
    event = {
        "body": json.dumps({
            "user_id":"u1",
            "filename":"x.png",
            "content_type":"image/png",
            "tags":["cats","cute"],
            "image_b64": base64.b64encode(img).decode()
        }),
        "isBase64Encoded": False
    }
    resp = upload_image(event, None)
    assert resp["statusCode"] == 201
    body = json.loads(resp["body"])
    assert "image_id" in body
    assert body["s3_key"].endswith("/x.png")
