import base64, json, os
from moto import mock_aws
from app.aws import s3, dynamodb

os.environ["BUCKET_NAME"] = "images"
os.environ["DDB_TABLE"] = "ImageMetadata"
os.environ["AWS_REGION"] = "us-east-1"

@mock_aws
def test_delete_image():
    from app.handlers import upload_image, delete_image, get_image

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

    img_b64 = base64.b64encode(b"data").decode()
    r = upload_image({"body": json.dumps({
        "user_id":"ux","filename":"del.png","content_type":"image/png","image_b64":img_b64
    })}, None)
    image_id = json.loads(r["body"])["image_id"]

    # delete
    d = delete_image({"pathParameters":{"image_id":image_id}}, None)
    assert d["statusCode"] == 204

    # now get should 404
    g = get_image({"pathParameters":{"image_id":image_id}, "queryStringParameters":{}}, None)
    assert g["statusCode"] == 404
