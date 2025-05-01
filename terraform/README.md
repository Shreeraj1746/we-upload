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
└── state-management/      # Resources for hosting remote state
    └── main.tf            # S3 and DynamoDB table for remote state
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

```bash
# Deploy to development environment (default)
./deploy.sh

# Deploy to production environment
./deploy.sh prod
```

Or manually deploy:

1. Navigate to the environment directory:
   ```bash
   cd terraform/environments/dev    # For development environment
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Plan changes:
   ```bash
   terraform plan
   ```

4. Apply changes:
   ```bash
   terraform apply
   ```

   When prompted, type "yes" to confirm the deployment.

### Creating a New Environment

To create a new environment (e.g., staging, testing):

1. Create a new directory under `environments/`:
   ```bash
   mkdir -p terraform/environments/staging
   ```

2. Copy the basic configuration files from an existing environment:
   ```bash
   cp terraform/environments/dev/{main.tf,variables.tf,outputs.tf} terraform/environments/staging/
   ```

3. Create a new `terraform.tfvars` file with environment-specific values:
   ```bash
   touch terraform/environments/staging/terraform.tfvars
   ```

4. Edit the `terraform.tfvars` file to set environment-specific values:
   ```hcl
   environment = "staging"
   # Set other environment-specific variables here
   ```

5. Follow the standard deployment instructions for the new environment.

### Verify Infrastructure

After deployment, verify the resources:

1. View Terraform outputs:
   ```bash
   terraform output
   ```

2. Check important resources:
   ```bash
   # EC2 instance
   aws ec2 describe-instances --filters "Name=tag:Name,Values=we-upload-*" --query "Reservations[].Instances[].{ID:InstanceId,State:State.Name,IP:PublicIpAddress}"

   # S3 bucket
   aws s3api list-buckets --query "Buckets[?contains(Name, 'we-upload')].Name"

   # RDS instance
   aws rds describe-db-instances --query "DBInstances[?contains(DBInstanceIdentifier, 'we-upload')].{ID:DBInstanceIdentifier,Status:DBInstanceStatus,Endpoint:Endpoint.Address}"
   ```

### Clean Up Resources

To destroy all resources and avoid unexpected charges:

```bash
# Navigate to the environment directory
cd terraform/environments/dev

# Destroy all resources
terraform destroy

# Confirm by typing "yes" when prompted
```

## Remote State Management

For team collaboration, we use remote state storage in S3 with state locking in DynamoDB:

### Setting Up Remote State

1. Navigate to the state-management directory:
   ```bash
   cd terraform/state-management
   ```

2. Deploy the state management infrastructure:
   ```bash
   terraform init
   terraform apply
   ```

3. Add backend configuration to your environment:
   ```hcl
   terraform {
     backend "s3" {
       bucket         = "we-upload-terraform-state"
       key            = "environments/dev/terraform.tfstate"
       region         = "ap-south-1"
       dynamodb_table = "we-upload-terraform-locks"
       encrypt        = true
     }
   }
   ```

4. Initialize with the new backend:
   ```bash
   terraform init -migrate-state
   ```

## Testing Resources

### Testing EC2 Instance

1. SSH into the EC2 instance:
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@$(terraform output -raw ec2_instance_public_ip)
   ```

2. Check Docker status:
   ```bash
   docker --version
   sudo systemctl status docker
   ```

### Testing RDS from EC2

1. Install PostgreSQL client:
   ```bash
   sudo apt-get update
   sudo apt-get install -y postgresql-client
   ```

2. Connect to the database:
   ```bash
   psql -h $(terraform output -raw rds_endpoint | cut -f1 -d:) \
        -p $(terraform output -raw rds_endpoint | cut -f2 -d:) \
        -U weuploadadmin \
        -d weupload
   ```

3. Test the connection:
   ```sql
   SELECT version();
   \q
   ```

## Troubleshooting

If you encounter issues:

1. **Error: No valid credential sources found**
   - Run `aws configure` to set up AWS credentials
   - Verify IAM permissions are correct

2. **Error: S3 bucket already exists**
   - Check if the bucket name is globally unique
   - Try a different bucket prefix in `terraform.tfvars`

3. **RDS connection issues**
   - Verify security group rules allow traffic from the EC2 instance
   - Check if the instance is in the correct subnet

4. **EC2 SSH access problems**
   - Verify key pair is correctly specified
   - Check security group rules for SSH access (port 22)

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

No providers.

## Modules

No modules.

## Resources

No resources.

## Inputs

No inputs.

## Outputs

No outputs.
<!-- END_TF_DOCS -->
