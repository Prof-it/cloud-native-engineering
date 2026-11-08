terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
resource "aws_kms_key" "statements" {
  enable_key_rotation = true
}
resource "aws_s3_bucket" "statements" {
  bucket = "lab-statements"
}
resource "aws_s3_bucket_server_side_encryption_configuration" "statements" {
  bucket = aws_s3_bucket.statements.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.statements.arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "statements" {
  bucket                  = aws_s3_bucket.statements.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "statements" {
  bucket = aws_s3_bucket.statements.id
  versioning_configuration {
    status = "Enabled"
  }
}
