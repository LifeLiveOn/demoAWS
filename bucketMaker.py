import boto3
import json

bucket_name = "flask-linktree-demo-images-2026"

s3 = boto3.client("s3", region_name="us-east-1")

# create bucket
s3.create_bucket(Bucket=bucket_name)

# define policy
policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadImages",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }
    ]
}

s3.put_public_access_block(
    Bucket=bucket_name,
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": False,
        "IgnorePublicAcls": False,
        "BlockPublicPolicy": False,
        "RestrictPublicBuckets": False
    }
)

# attach policy
s3.put_bucket_policy(
    Bucket=bucket_name,
    Policy=json.dumps(policy)
)
