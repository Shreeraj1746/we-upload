# We-Upload Terraform Infrastructure

This directory contains the Terraform configuration for deploying the We-Upload application infrastructure to AWS. The infrastructure is designed to stay within AWS Free Tier limits.

## Directory Structure

```
terraform/
├── main.tf                # Main Terraform configuration
├── provider.tf            # AWS provider configuration
├── variables.tf           # Root module variables
├── outputs.tf             # Root module outputs
├── modules/               # Reusable Terraform modules
│   ├── vpc/               # VPC module
│   ├── s3/                # S3 bucket module
│   └── iam/               # IAM roles and policies module
└── environments/          # Environment-specific configurations
    └── dev/               # Development environment
```

## Modules

### VPC Module
Creates a Virtual Private Cloud (VPC) with:
- Public and private subnets across multiple availability zones
- Internet Gateway for public subnet access
- NAT Gateway for private subnet outbound access
- Route tables for network traffic management

### S3 Module
Sets up S3 bucket for file storage with:
- Proper access controls
- Security configurations
- Lifecycle policies

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

1. Navigate to the environment directory you want to deploy:
   ```
   cd terraform/environments/dev
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

### Verify Infrastructure

After successful deployment, you can verify the resources using AWS CLI or Terraform output:

1. View Terraform outputs:
   ```
   terraform output
   ```

2. Verify VPC and network components:
   ```
   aws ec2 describe-vpcs --vpc-ids $(terraform output -raw vpc_id)
   aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)"
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

To avoid incurring AWS charges, it's important to clean up resources when they're no longer needed:

1. Run the destroy command:
   ```
   terraform destroy
   ```

2. Review the resources that will be destroyed and type "yes" when prompted to confirm.

3. Verify that all resources have been properly destroyed:
   ```
   terraform output
   ```

## Testing EC2 and RDS Resources

After deploying the infrastructure, you can test that the EC2 instance and RDS PostgreSQL instance are working correctly:

#### Testing EC2 Instance

1. SSH into the EC2 instance:
   ```
   ssh -i /path/to/private/key ec2-user@$(terraform output -raw ec2_instance_public_ip)
   ```

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

2. Connect to the RDS instance:
   ```
   psql -h $(terraform output -raw rds_endpoint | cut -f1 -d:) \
        -p $(terraform output -raw rds_endpoint | cut -f2 -d:) \
        -U weuploadadmin \
        -d weupload
   ```

3. When prompted, enter the database password you specified in the Terraform variables.

4. Test the PostgreSQL connection with:
   ```
   SELECT version();
   ```

5. Exit the PostgreSQL client:
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
