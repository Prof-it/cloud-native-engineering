resource "aws_s3_bucket" "statements" {
  bucket = "lab-statements"
}
resource "aws_s3_bucket_public_access_block" "statements" {
  bucket                  = aws_s3_bucket.statements.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
