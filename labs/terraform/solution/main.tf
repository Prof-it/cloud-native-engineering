terraform {
  required_version = ">= 1.6.0"
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

provider "local" {}

variable "artifact_name" {
  type        = string
  description = "Name of generated file"
  default     = "solution.txt"
}

resource "local_file" "solution" {
  content  = "terraform solution artifact"
  filename = "./${var.artifact_name}"
}

output "artifact_path" {
  value = local_file.solution.filename
}
