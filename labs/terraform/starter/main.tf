terraform {
  required_version = ">= 1.6.0"
}

resource "local_file" "starter" {
  content  = "starter artifact"
  filename = "./starter.txt"
}
