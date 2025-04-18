#!/bin/bash
set -e

# Initialize Terragrunt setup by creating the required S3 bucket and DynamoDB table

# Configuration
TF_STATE_BUCKET="${TF_STATE_BUCKET:-we-upload-terraform-state}"
TF_LOCK_TABLE="${TF_LOCK_TABLE:-we-upload-terraform-locks}"
AWS_REGION="${AWS_REGION:-us-east-1}"

echo "Creating Terraform state bucket: $TF_STATE_BUCKET"
# us-east-1 doesn't need LocationConstraint
if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket \
        --bucket "$TF_STATE_BUCKET" \
        --region "$AWS_REGION"
else
    aws s3api create-bucket \
        --bucket "$TF_STATE_BUCKET" \
        --region "$AWS_REGION" \
        --create-bucket-configuration LocationConstraint="$AWS_REGION"
fi

# Enable versioning on the bucket
aws s3api put-bucket-versioning \
    --bucket "$TF_STATE_BUCKET" \
    --versioning-configuration Status=Enabled

# Enable encryption on the bucket
aws s3api put-bucket-encryption \
    --bucket "$TF_STATE_BUCKET" \
    --server-side-encryption-configuration '{
        "Rules": [
            {
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }
        ]
    }'

# Block public access to the bucket
aws s3api put-public-access-block \
    --bucket "$TF_STATE_BUCKET" \
    --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

echo "Creating DynamoDB table for state locking: $TF_LOCK_TABLE"
aws dynamodb create-table \
    --table-name "$TF_LOCK_TABLE" \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region "$AWS_REGION"

echo "Terragrunt infrastructure initialized successfully!"
echo "  State bucket: $TF_STATE_BUCKET"
echo "  Lock table: $TF_LOCK_TABLE"
echo "  Region: $AWS_REGION"
echo ""
echo "Usage:"
echo "  cd terragrunt/dev/vpc"
echo "  terragrunt plan"
echo "  terragrunt apply"
