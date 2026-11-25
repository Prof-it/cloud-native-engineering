# Realms as code for the identity platform lab.
# Pinned: provider keycloak/keycloak 5.11.0 (Keycloak 26.x). Secrets reach
# Keycloak only through write-only arguments fed by ephemeral variables, so
# they are in neither plan nor state; that needs Terraform >= 1.11 (OpenTofu:
# a release with ephemeral variables and write-only arguments).
terraform {
  required_version = ">= 1.11.0"
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "= 5.11.0"
    }
  }
}

# Local track: password grant of the bootstrap admin, passed as KEYCLOAK_USER /
# KEYCLOAK_PASSWORD by scripts/live-up.sh. Production: a confidential client in
# the master realm with only the roles this code needs.
provider "keycloak" {
  url       = var.keycloak_url
  client_id = "admin-cli"
}
