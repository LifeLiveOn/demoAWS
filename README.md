# Flask LinkTree Demo on AWS

This project is a simple Flask application that demonstrates how to use AWS services in a small web app and how to deploy that app from GitHub Actions to AWS App Runner.

The demo uses:

- AWS App Runner to host the containerized Flask app
- Amazon S3 to store uploaded profile images
- Amazon DynamoDB to store user profiles and links
- IAM to grant deployment access from GitHub Actions and runtime access from App Runner

## Architecture

The application flow is:

1. A user creates a profile in the Flask app.
2. Profile metadata is stored in DynamoDB.
3. Profile images are uploaded to S3.
4. The app runs inside a Docker container on App Runner.
5. GitHub Actions builds and deploys the application.

## Project Layout

- [app/app.py](app/app.py): Flask application entry point
- [app/routes.py](app/routes.py): Routes for profiles, links, and image uploads
- [app/aws.py](app/aws.py): boto3 clients for DynamoDB and S3
- [Dockerfile](Dockerfile): Container image for App Runner
- [table_bucket_maker.sh](table_bucket_maker.sh): AWS CLI helper to create the S3 bucket and DynamoDB tables
- [sample.env](sample.env): Example environment variables for local development

## AWS Services Used

### App Runner

App Runner hosts the Flask app container and exposes it as a web service.

### DynamoDB

Two tables are used:

- `users`: stores one item per username
- `links`: stores multiple links per username using a composite key

### S3

S3 stores uploaded profile images.

### IAM

IAM is used in two separate ways:

1. GitHub Actions deployment credentials
2. App Runner runtime permissions

These are different responsibilities and should not be mixed.

## IAM Setup

### Option Used in This Demo: IAM User Access Keys for GitHub Actions

For the purpose of demo

1. Create an IAM user for GitHub Actions deployment.
2. Attach a limited policy that allows pushing images and updating App Runner.
3. Generate an access key and secret access key.
4. Store them in GitHub repository secrets.

Recommended GitHub secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`
- `ECR_REPOSITORY`
- `APP_RUNNER_SERVICE_ARN`
- `S3_BUCKET_NAME`

Important: For production the better pattern is GitHub OIDC with an assumable IAM role .

### App Runner Runtime IAM Role

App Runner itself should use an IAM role so the deployed app can talk to DynamoDB and S3 without embedding AWS keys in the container.

That role should allow at least:

- `dynamodb:GetItem`
- `dynamodb:PutItem`
- `dynamodb:UpdateItem`
- `dynamodb:Query`
- `s3:GetObject`
- `s3:PutObject`

If you later add delete features, also include:

- `s3:DeleteObject`

## Create the AWS Resources

You can create the bucket and tables with the included shell script:

```sh
sh table_bucket_maker.sh
```

The script uses:

- `S3_BUCKET_NAME`
- `AWS_DEFAULT_REGION`
- `USERS_TABLE_NAME` with default `users`
- `LINKS_TABLE_NAME` with default `links`

Example:

```sh
S3_BUCKET_NAME=flask-linktree-demo-images-2026 AWS_DEFAULT_REGION=us-east-1 sh table_bucket_maker.sh
```

## Local Environment Variables

Example local `.env` values:

```env
S3_BUCKET_NAME=flask-linktree-demo-images-2026
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Build the Docker Image

Build locally:

```sh
docker build -t flask-linktree-demo .
```

Run locally:

```sh
docker run --rm -p 8000:8000 --env-file .env flask-linktree-demo
```

Then open:

```text
http://localhost:8000/
```

## GitHub Actions Deployment Flow

The deployment flow is:

1. GitHub Actions checks out the code.
2. GitHub Actions authenticates to AWS using IAM access keys stored in GitHub Secrets.
3. The workflow logs in to Amazon ECR.
4. The Docker image is built and pushed to ECR.
5. App Runner is updated to use the new image.

## Example GitHub Actions Workflow

Add a workflow at [.github/workflows/deploy.yml](.github/workflows/deploy.yml):

```yaml
name: Deploy to AWS App Runner

on:
	push:
		branches:
			- main

jobs:
	deploy:
		runs-on: ubuntu-latest

		steps:
			- name: Checkout
				uses: actions/checkout@v4

			- name: Configure AWS credentials
				uses: aws-actions/configure-aws-credentials@v4
				with:
					aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
					aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
					aws-region: ${{ secrets.AWS_REGION }}

			- name: Login to Amazon ECR
				id: login-ecr
				uses: aws-actions/amazon-ecr-login@v2

			- name: Build and push Docker image
				env:
					ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
					ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
					IMAGE_TAG: ${{ github.sha }}
				run: |
					docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
					docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

			- name: Update App Runner service
				env:
					ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
					ECR_REPOSITORY: ${{ secrets.ECR_REPOSITORY }}
					IMAGE_TAG: ${{ github.sha }}
					APP_RUNNER_SERVICE_ARN: ${{ secrets.APP_RUNNER_SERVICE_ARN }}
				run: |
					aws apprunner update-service \
						--service-arn $APP_RUNNER_SERVICE_ARN \
						--source-configuration ImageRepository="{ImageIdentifier=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG,ImageRepositoryType=ECR}",AutoDeploymentsEnabled=true
```

## App Runner Configuration

When creating the App Runner service:

1. Use the image from Amazon ECR.
2. Set the runtime port to `8000`.
3. Add environment variables:
   - `S3_BUCKET_NAME`
   - `AWS_DEFAULT_REGION=us-east-1`
   - `SECRET_KEY`
4. Attach an IAM role that grants access to S3 and DynamoDB.

Note: do not provide `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` to App Runner if you already attached an IAM role.

## Example IAM Permissions

### GitHub Actions IAM User

The GitHub Actions deployment identity needs access to:

- ECR push actions
- App Runner update actions
- IAM PassRole if App Runner needs to use a service role

### App Runner IAM Role

Example permissions scope:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/users",
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/links"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::flask-linktree-demo-images-2026/*"
    }
  ]
}
```

## Teaching Notes

This repo is useful for demonstrating:

- how a Flask app uses `boto3` to talk to AWS
- how GitHub Actions deploys a container to App Runner
- how S3 stores uploaded objects
- how DynamoDB stores structured application data
- how IAM separates deployment access from runtime application access

## Recommended Improvement for Production

For a production-ready pipeline, prefer:

1. GitHub OIDC instead of long-lived IAM user access keys
2. App Runner IAM roles instead of runtime AWS access keys
3. Secrets Manager or SSM Parameter Store for sensitive configuration
4. Principle of least privilege for every IAM policy

# useful command
aws ecr create-repository \
  --repository-name my-repo \
  --region us-east-1

