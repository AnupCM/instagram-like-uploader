import os
import boto3

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
IS_LOCAL = os.getenv("IS_LOCAL", "false").lower() in ("1", "true", "yes")

def _endpoint(service: str):
    if IS_LOCAL:
        # LocalStack default edge endpoint
        return os.getenv("LOCALSTACK_URL", "http://localhost:4566")
    return None

def s3():
    return boto3.client("s3", region_name=AWS_REGION, endpoint_url=_endpoint("s3"))

def dynamodb():
    return boto3.resource("dynamodb", region_name=AWS_REGION, endpoint_url=_endpoint("dynamodb"))
