#!/usr/bin/env sh

set -eu

REGION="${AWS_DEFAULT_REGION:-us-east-1}"
BUCKET_NAME="${S3_BUCKET_NAME:-flask-linktree-demo-images-2026}"
USERS_TABLE_NAME="${USERS_TABLE_NAME:-users}"
LINKS_TABLE_NAME="${LINKS_TABLE_NAME:-links}"

if [ "$REGION" = "us-east-1" ]; then
	aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION"
else
	aws s3api create-bucket --bucket "$BUCKET_NAME" --region "$REGION" --create-bucket-configuration "LocationConstraint=$REGION"
fi

aws s3api put-public-access-block \
	--bucket "$BUCKET_NAME" \
	--public-access-block-configuration BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

aws s3api put-bucket-policy \
	--bucket "$BUCKET_NAME" \
	--policy "{
	  \"Version\": \"2012-10-17\",
	  \"Statement\": [
		{
		  \"Sid\": \"PublicReadImages\",
		  \"Effect\": \"Allow\",
		  \"Principal\": \"*\",
		  \"Action\": \"s3:GetObject\",
		  \"Resource\": \"arn:aws:s3:::$BUCKET_NAME/*\"
		}
	  ]
	}"

aws dynamodb create-table \
	--table-name "$USERS_TABLE_NAME" \
	--attribute-definitions AttributeName=username,AttributeType=S \
	--key-schema AttributeName=username,KeyType=HASH \
	--billing-mode PAY_PER_REQUEST \
	--region "$REGION"

aws dynamodb create-table \
	--table-name "$LINKS_TABLE_NAME" \
	--attribute-definitions AttributeName=username,AttributeType=S AttributeName=link_id,AttributeType=S \
	--key-schema AttributeName=username,KeyType=HASH AttributeName=link_id,KeyType=RANGE \
	--billing-mode PAY_PER_REQUEST \
	--region "$REGION"

echo "Bucket and tables created."
