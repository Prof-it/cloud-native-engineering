# Starter: the platform realm as a team first wrote it, "to get it working".
# It applies without error and every login works. tests/fixtures/plan-flawed.json
# is the plan of this code. Run the guardrails against it (step 3), then fix
# this file until your plan would pass; compare with solution/live/terraform.

variable "keycloak_url" {
  type    = string
  default = "http://keycloak.localtest.me:8080"
}

variable "public_url" {
  type    = string
  default = "http://keycloak.localtest.me:8080"
}

resource "keycloak_realm" "platform" {
  realm        = "platform"
  enabled      = true
  ssl_required = "none"           # TODO G8

  access_token_lifespan   = "30m" # TODO G6: "so that users are not logged out"
  revoke_refresh_token    = false # TODO G7
  refresh_token_max_reuse = 0
  # TODO G9: no brute-force detection
}

resource "keycloak_oidc_identity_provider" "corporate" {
  realm             = keycloak_realm.platform.id
  alias             = "corporate"
  authorization_url = "${var.public_url}/realms/corporate/protocol/openid-connect/auth"
  token_url         = "${var.public_url}/realms/corporate/protocol/openid-connect/token"
  client_id         = "platform-broker"
  client_secret     = "broker-secret-from-the-wiki" # also lands in the state
  validate_signature = false                         # TODO G12
  trust_email        = true                          # TODO G12
}

resource "keycloak_openid_client" "portal_web" {
  realm_id              = keycloak_realm.platform.id
  client_id             = "portal-web"
  access_type           = "PUBLIC"
  standard_flow_enabled = true
  implicit_flow_enabled = true # TODO G2: left over from an old SPA library
  # TODO G1: no PKCE
  valid_redirect_uris = [
    "https://portal.example.org/*",       # TODO G4
    "http://portal.example.org/callback", # TODO G4
  ]
  web_origins = ["*"] # TODO G5
  # TODO G11: full_scope_allowed defaults to true
}

resource "keycloak_openid_client" "benefits_api" {
  realm_id                     = keycloak_realm.platform.id
  client_id                    = "benefits-api"
  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = false
  direct_access_grants_enabled = true # TODO G3: "for the integration tests"
  service_accounts_enabled     = true
}

resource "keycloak_openid_client" "claims_worker" {
  realm_id                 = keycloak_realm.platform.id
  client_id                = "claims-worker"
  access_type              = "CONFIDENTIAL"
  standard_flow_enabled    = false
  service_accounts_enabled = true
  client_secret            = "w0rker-s3cret" # TODO G10: shared secret, and in the state
}
