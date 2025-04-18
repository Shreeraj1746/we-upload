# Terragrunt Configuration for We-Upload

This directory contains the Terragrunt configuration for the We-Upload project. Terragrunt is used as a thin wrapper around Terraform to provide additional features like:

- DRY (Don't Repeat Yourself) infrastructure code
- Remote state management
- Module dependencies
- Environment-specific configurations

## Structure

```
terragrunt/
├── terragrunt.hcl         # Root configuration for all environments
├── dev/                   # Development environment configuration
│   ├── env.hcl            # Environment-specific variables
│   ├── terragrunt.hcl     # Environment configuration
│   ├── vpc/               # VPC module configuration
│   ├── s3/                # S3 module configuration
│   └── app/               # App module configuration
└── prod/                  # Production environment configuration
    ├── env.hcl            # Environment-specific variables
    └── terragrunt.hcl     # Environment configuration
```

## Setup

Before using Terragrunt, you need to set up the required AWS infrastructure:

1. Run the initialization script:
   ```bash
   ./scripts/init-terragrunt.sh
   ```

2. Set environment variables:
   ```bash
   export TF_VAR_db_password="your-secure-password"
   export TF_VAR_api_secret_key="your-api-secret-key"
   export TF_VAR_ecr_repository="your-ecr-repo-url"
   export TF_VAR_random_suffix="unique-suffix-for-s3"  # Or let it generate a UUID
   ```

## Usage

1. To plan or apply a specific module:
   ```bash
   cd terragrunt/dev/vpc
   terragrunt plan
   terragrunt apply
   ```

2. To plan or apply all modules in an environment:
   ```bash
   cd terragrunt/dev
   terragrunt run-all plan
   terragrunt run-all apply
   ```

3. To plan or apply a specific module in all environments:
   ```bash
   cd terragrunt
   terragrunt run-all plan --terragrunt-working-dir */vpc
   ```

## Best Practices

1. Never store sensitive information in the code; use environment variables or AWS Secrets Manager
2. Always run `terragrunt plan` before applying changes
3. Use consistent naming across environments
4. Keep environment configurations as similar as possible to minimize differences
5. Use mock outputs for module dependencies to enable validation without applying changes

## Dependencies

The modules have the following dependencies:

- `app` depends on `vpc` and `s3`
- `s3` has no dependencies
- `vpc` has no dependencies
