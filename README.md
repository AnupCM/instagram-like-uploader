# Instagram-like Image Upload Service

This project implements a simplified service layer for an Instagram-like application.  
It provides APIs for **image upload, storage in S3, metadata persistence in DynamoDB, and retrieval/deletion**.  
The service is built on **AWS Lambda + API Gateway + S3 + DynamoDB**, with **LocalStack** for local development.

---

## 🚀 Features
1. **Upload Image** with metadata (user, caption, tags, etc.).
2. **List Images** with filters (e.g., by user, by tag).
3. **View/Download Image**.
4. **Delete Image** (removes from S3 + metadata from DynamoDB).
5. **Scalable & Serverless** using AWS Lambda.
6. **Unit Tests** for all major scenarios.

---

## 🛠️ Tech Stack
- **Language:** Python 3.7+
- **AWS Services:** S3, DynamoDB, API Gateway, Lambda
- **Local Development:** LocalStack (via Docker Compose)
- **Testing:** pytest, moto (mock AWS services)

---

## ⚙️ Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/your-repo/instagram-image-service.git
cd instagram-image-service
```

1.Start LocalStack

Make sure you have Docker and docker-compose installed.
docker-compose up


2. This starts LocalStack with s3, dynamodb, apigateway, and lambda.

3. Configure AWS CLI for LocalStack
aws configure
# Use dummy values
AWS Access Key ID: test
AWS Secret Access Key: test
Default region: us-east-1


Set the endpoint when calling AWS services:

--endpoint-url=http://localhost:4566

4. Deploy Resources
./scripts/deploy.sh


This script will:

Create an S3 bucket images-bucket.

Create a DynamoDB table images_metadata.

Deploy Lambda functions.

Create API Gateway endpoints.

📡 API Endpoints
1. Upload Image

POST /images

Request:

Multipart form data with:

file: image file

metadata: JSON metadata (e.g., user_id, caption, tags)

Response:

{
  "image_id": "uuid",
  "message": "Image uploaded successfully"
}

2. List Images

GET /images?user_id=123&tag=travel

Query Params:

user_id (optional)

tag (optional)

Response:

[
  {
    "image_id": "uuid",
    "user_id": "123",
    "caption": "Beach vibes",
    "tags": ["travel", "beach"],
    "url": "https://s3.localhost/.../uuid.jpg"
  }
]

3. View/Download Image

GET /images/{image_id}

Response:
Returns a presigned URL to download the image.

4. Delete Image

DELETE /images/{image_id}

Response:

{
  "message": "Image deleted successfully"
}

🧪 Running Tests

Install dependencies:

pip install -r requirements.txt


Run unit tests:

pytest tests/

📖 API Documentation

After deploying, view API Gateway documentation at:

http://localhost:4566/restapis/<api-id>/<stage>/_user_request_/


Alternatively, check the docs/api_documentation.md file.

📂 Project Structure
.
├── lambdas/
│   ├── upload_image.py
│   ├── list_images.py
│   ├── view_image.py
│   ├── delete_image.py
├── tests/
│   ├── test_upload.py
│   ├── test_list.py
│   ├── test_view.py
│   ├── test_delete.py
├── scripts/
│   └── deploy.sh
├── docker-compose.yml
├── requirements.txt
└── README.md

