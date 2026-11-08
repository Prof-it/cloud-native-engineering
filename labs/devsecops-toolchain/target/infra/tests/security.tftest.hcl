mock_provider "aws" {}

run "kms_rotation_enabled" {
  command = plan
  assert {
    condition     = aws_kms_key.statements.enable_key_rotation == true
    error_message = "KMS key rotation must be enabled"
  }
}

run "bucket_uses_kms" {
  command = plan
  assert {
    condition     = one(one(aws_s3_bucket_server_side_encryption_configuration.statements.rule).apply_server_side_encryption_by_default).sse_algorithm == "aws:kms"
    error_message = "Bucket must use aws:kms"
  }
}

run "statements_bucket_not_public" {
  command = plan
  assert {
    condition = alltrue([
      aws_s3_bucket_public_access_block.statements.block_public_acls,
      aws_s3_bucket_public_access_block.statements.block_public_policy,
      aws_s3_bucket_public_access_block.statements.ignore_public_acls,
      aws_s3_bucket_public_access_block.statements.restrict_public_buckets,
    ])
    error_message = "The statements bucket must block all public access"
  }
}

run "statements_bucket_versioned" {
  command = plan
  assert {
    condition     = aws_s3_bucket_versioning.statements.versioning_configuration[0].status == "Enabled"
    error_message = "The statements bucket must be versioned"
  }
}
