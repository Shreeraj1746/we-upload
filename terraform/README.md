# We-Upload Terraform Infrastructure

This directory contains the Terraform configuration for deploying the We-Upload application infrastructure to AWS. The infrastructure is designed to stay within AWS Free Tier limits.

## Directory Structure

```
terraform/
├── modules/               # Reusable Terraform modules
│   ├── vpc/               # VPC module
│   ├── s3/                # S3 bucket module
│   ├── ec2/               # EC2 instance module
│   ├── rds/               # RDS database module
│   └── iam/               # IAM roles and policies module
├── environments/          # Environment-specific configurations
│   ├── dev/               # Development environment
│   │   ├── main.tf        # Main configuration for dev
│   │   ├── variables.tf   # Variables specific to dev
│   │   ├── outputs.tf     # Outputs specific to dev
│   │   └── terraform.tfvars # Variable values for dev
│   └── prod/              # Production environment
│       ├── main.tf        # Main configuration for prod
│       ├── variables.tf   # Variables specific to prod
│       ├── outputs.tf     # Outputs specific to prod
│       └── terraform.tfvars # Variable values for prod
├── deploy.sh              # Deployment script
└── cleanup.sh             # Cleanup script
```

## Modules

### VPC Module
Creates a Virtual Private Cloud (VPC) with:
- Public and private subnets across multiple availability zones
- Internet Gateway for public subnet access
- NAT Gateway for private subnet outbound access (can be disabled)
- Route tables for network traffic management

### S3 Module
Sets up S3 bucket for file storage with:
- Proper access controls
- Security configurations
- Lifecycle policies

### EC2 Module
Provisions EC2 instances with:
- Appropriate security groups
- IAM instance profile
- User data for bootstrap configuration

### RDS Module
Sets up RDS PostgreSQL database with:
- Proper subnet groups
- Security groups
- Parameter groups

### IAM Module
Configures necessary IAM roles and policies for:
- EC2 instances to access S3
- Services to interact with each other

## Free Tier Considerations

All resources are configured to stay within AWS Free Tier limits:
- VPC and its components are free
- S3 is configured to stay within the 5GB free storage limit
- NAT Gateway will be **disabled** as it's not included in the Free Tier
- EC2 uses t2.micro instance type (750 hours/month free)
- RDS uses db.t3.micro instance type with minimal storage (750 hours/month free)

### Cost-Saving Measures

This implementation takes specific measures to keep costs at $0:

1. **No NAT Gateway**: The NAT Gateway is explicitly disabled (`create_nat_gateway = false`) as it incurs hourly charges.
   - Note: This means instances in private subnets won't have outbound internet access
   - The RDS instance in the private subnet works fine without internet access
   - Any instances requiring outbound internet access should be placed in public subnets

2. **Free Tier Instance Types**: Using only t2.micro for EC2 and db.t3.micro for RDS

3. **Minimal Storage**: Configuring minimal storage requirements while maintaining functionality

## Deployment Instructions

### Prerequisites
1. Install Terraform (v1.0.0 or later): https://developer.hashicorp.com/terraform/install
2. AWS CLI installed and configured with proper credentials: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
3. Configure AWS credentials with the appropriate permissions:
   ```
   aws configure
   ```

### Deploy Infrastructure

You can use the provided deployment script:

```
# Deploy to development environment (default)
./deploy.sh

# Deploy to production environment
./deploy.sh prod
```

Or manually:

1. Navigate to the environment directory you want to deploy:
   ```
   cd terraform/environments/dev    # For development environment
   # OR
   cd terraform/environments/prod   # For production environment
   ```

2. Initialize Terraform:
   ```
   terraform init
   ```

3. Plan changes to verify what resources will be created:
   ```
   terraform plan
   ```

4. Apply changes to create the infrastructure:
   ```
   terraform apply
   ```

   When prompted, type "yes" to confirm the deployment.

### Creating a New Environment

To create a new environment (e.g., staging, testing):

1. Create a new directory under `environments/`:
   ```
   mkdir -p terraform/environments/staging
   ```

2. Copy the basic configuration files from an existing environment:
   ```
   cp terraform/environments/dev/{main.tf,variables.tf,outputs.tf} terraform/environments/staging/
   ```

3. Create a new `terraform.tfvars` file with environment-specific values:
   ```
   touch terraform/environments/staging/terraform.tfvars
   ```

4. Edit the `terraform.tfvars` file to set environment-specific values:
   ```
   environment = "staging"
   # Set other environment-specific variables here
   ```

5. Customize `main.tf` as needed for the new environment.

6. Follow the standard deployment instructions for the new environment.

### Verify Infrastructure

After successful deployment, you can verify the resources using AWS CLI or Terraform output:

1. View Terraform outputs:
   ```
   terraform output
   ```

2. Verify VPC and network components:
   ```
   aws ec2 describe-vpcs --vpc-ids $(terraform output -raw vpc_id)
   aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id"
   aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)"
   ```

3. Verify S3 bucket:
   ```
   aws s3api get-bucket-encryption --bucket $(terraform output -raw s3_bucket_name)
   aws s3api get-bucket-lifecycle-configuration --bucket $(terraform output -raw s3_bucket_name)
   ```

4. Verify IAM roles and policies:
   ```
   aws iam get-role --role-name $(terraform output -raw ec2_role_name)
   aws iam list-attached-role-policies --role-name $(terraform output -raw ec2_role_name)
   ```

### Clean Up Resources

You can use the provided cleanup script:

```
# Clean up development environment (default)
./cleanup.sh

# Clean up production environment
./cleanup.sh prod
```

Or manually:

1. Navigate to the environment directory:
   ```
   cd terraform/environments/dev    # For development environment
   ```

2. Run the destroy command:
   ```
   terraform destroy
   ```

3. Review the resources that will be destroyed and type "yes" when prompted to confirm.

4. Verify that all resources have been properly destroyed:
   ```
   terraform output
   ```

## Remote State Management

Each environment manages its own state file. For collaboration and backup, it's recommended to configure remote state storage:

### Setting Up Remote State

1. Create an S3 bucket for storing Terraform state:
   ```
   aws s3api create-bucket \
       --bucket we-upload-terraform-state \
       --region ap-south-1 \
       --create-bucket-configuration LocationConstraint=ap-south-1
   ```

2. Enable versioning and encryption:
   ```
   aws s3api put-bucket-versioning \
       --bucket we-upload-terraform-state \
       --versioning-configuration Status=Enabled

   aws s3api put-bucket-encryption \
       --bucket we-upload-terraform-state \
       --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
   ```

3. Create a DynamoDB table for state locking:
   ```
   aws dynamodb create-table \
       --table-name we-upload-terraform-locks \
       --attribute-definitions AttributeName=LockID,AttributeType=S \
       --key-schema AttributeName=LockID,KeyType=HASH \
       --billing-mode PAY_PER_REQUEST \
       --region ap-south-1
   ```

4. Add the following to each environment's `main.tf` file:
   ```hcl
   terraform {
     backend "s3" {
       bucket         = "we-upload-terraform-state"
       key            = "environments/<environment>/terraform.tfstate" # e.g., "environments/dev/terraform.tfstate"
       region         = "ap-south-1"
       dynamodb_table = "we-upload-terraform-locks"
       encrypt        = true
     }
   }
   ```

5. Replace `<environment>` with the specific environment name (e.g., "dev", "prod").

6. Initialize Terraform with the backend configuration:
   ```
   terraform init
   ```

This setup ensures:
- State is securely stored in S3 with encryption
- State locking to prevent concurrent modifications
- Version history for the state files

## Testing EC2 and RDS Resources

After deploying the infrastructure, you can test that the EC2 instance and RDS PostgreSQL instance are working correctly:

#### Testing EC2 Instance

1. SSH into the EC2 instance:
   ```
   ssh -i /path/to/private/key ec2-user@$(terraform output -raw ec2_instance_public_ip)
   ```
   Note: You can also connect to the EC2 instance via Session Manager if you don't have a ssh_key.

2. Verify Docker is installed and running:
   ```
   docker --version
   sudo systemctl status docker
   ```

#### Testing RDS Instance from EC2

1. Install PostgreSQL client on the EC2 instance:
   ```
   sudo apt-get update
   sudo apt-get install -y postgresql-client
   ```

2. Install Terraform:
   ```
   wget -O - https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
   sudo apt update && sudo apt install terraform
   ```

3. Connect to the RDS instance:
   ```
   psql -h $(terraform output -raw rds_endpoint | cut -f1 -d:) \
        -p $(terraform output -raw rds_endpoint | cut -f2 -d:) \
        -U weuploadadmin \
        -d weupload
   ```

4. When prompted, enter the database password you specified in the Terraform variables.

5. Test the PostgreSQL connection with:
   ```
   SELECT version();
   ```

6. Exit the PostgreSQL client:
   ```
   \q
   ```

### Security Note

This testing setup is for development purposes. In production, you should:
1. Use more restrictive security groups
2. Store database credentials in AWS Secrets Manager
3. Implement proper encryption for all data in transit and at rest

## Troubleshooting

Common issues and their solutions:

1. **Error: NoCredentialProviders**
   - Make sure AWS CLI is configured with proper credentials using `aws configure`
   - Verify that your credentials have appropriate permissions

2. **Error: Resource already exists**
   - Resources with the same name might already exist in your AWS account
   - Use the AWS console to check for existing resources or modify resource naming

3. **Deployment takes too long or times out**
   - Check your internet connection
   - Some AWS resources (like S3 bucket lifecycle configurations) can take time to propagate
   - Try running the operation again

4. **Error: Failed to destroy some resources**
   - Some resources might have dependencies that were not tracked by Terraform
   - Check the AWS console and manually delete any remaining resources
