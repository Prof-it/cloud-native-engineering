# Terraform Labs

## Objective

Understand and apply the fundamentals of Infrastructure as Code (IaC) by provisioning resources using Terraform in a vendor-neutral environment.

## Prerequisites

- [Terraform CLI](https://www.terraform.io/downloads.html) installed
- Basic command-line proficiency
- (Optional) Cloud provider account (e.g., AWS, Azure, GCP) or use [Local provider](https://registry.terraform.io/providers/hashicorp/local/latest/docs)

## Scenario

You are tasked with provisioning infrastructure using Terraform. This lab will guide you through writing a Terraform configuration to create a local file and, optionally, a cloud resource. You will learn how to initialize, plan, apply, and destroy Terraform-managed infrastructure.

## Steps

1. **Create a New Directory for the Lab**
   ```sh
   mkdir terraform-lab
   cd terraform-lab
   ```

2. **Write a Simple Terraform Configuration**
   - Create a file named `main.tf` with the following content to create a local file:
     ```hcl
     terraform {
       required_providers {
         local = {
           source  = "hashicorp/local"
           version = "~> 2.0"
         }
       }
     }

     provider "local" {}

     resource "local_file" "example" {
       content  = "Hello, Terraform!"
       filename = "${path.module}/hello.txt"
     }
     ```

3. **Initialize Terraform**
   ```sh
   terraform init
   ```

4. **Plan the Infrastructure**
   ```sh
   terraform plan
   ```

5. **Apply the Configuration**
   ```sh
   terraform apply -auto-approve
   ```

6. **Verify the Resource**
   - Check that `hello.txt` exists and contains "Hello, Terraform!".

7. **(Optional) Provision a Cloud Resource**
   - Update `main.tf` to add a resource for your preferred cloud provider (see [Terraform Registry](https://registry.terraform.io/)).

## Validation

- `hello.txt` is created with the expected content.
- `terraform plan` and `terraform apply` complete without errors.
- (Optional) Cloud resource is provisioned as expected.

## Common Failure Modes

- **Provider plugin errors:** Ensure you have internet access for `terraform init`.
- **Permission errors:** Check directory permissions.
- **Cloud resource errors:** Verify credentials and region settings for your cloud provider.

## Cleanup

- Destroy resources:
  ```sh
  terraform destroy -auto-approve
  ```
- Remove the lab directory:
  ```sh
  cd ..
  rm -rf terraform-lab
  ```

## Related Topics

- [Cloud-Native Patterns: Infrastructure as Code](../../patterns/infrastructure-as-code.md)
- [Case Studies: Google Cloud Automation](../../case-studies/google/README.md)
- [Learning Path: Infrastructure as Code](../../docs/07-cloud-native-architecture.md)
- [Glossary](../../docs/glossary.md)
- [Open Source Projects](../../resources/open-source-projects.md)

---

**Next Lab:** Proceed to [labs/gitops/README.md](../gitops/README.md) to learn about declarative delivery and operations.