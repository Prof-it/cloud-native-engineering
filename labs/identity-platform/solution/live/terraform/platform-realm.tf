# The platform realm: the one issuer every API of the platform trusts.
# Rules from the case: short access tokens (I5), rotating refresh tokens,
# TLS outside the cluster, brute-force detection, no realm deleted by a typo.

resource "keycloak_realm" "platform" {
  realm        = "platform"
  enabled      = true
  display_name = "Identity platform"
  ssl_required = "external"

  access_token_lifespan    = "5m"
  sso_session_idle_timeout = "30m"
  sso_session_max_lifespan = "10h"
  revoke_refresh_token     = true
  refresh_token_max_reuse  = 0

  default_signature_algorithm = "RS256"

  # Set to true outside the lab: a destroy plan then fails instead of deleting
  # every user, session and client of the realm.
  terraform_deletion_protection = false

  security_defenses {
    headers {
      x_frame_options                     = "DENY"
      content_security_policy             = "frame-src 'self'; frame-ancestors 'self'; object-src 'none';"
      content_security_policy_report_only = ""
      x_content_type_options              = "nosniff"
      x_robots_tag                        = "none"
      x_xss_protection                    = "1; mode=block"
      strict_transport_security           = "max-age=31536000; includeSubDomains"
      referrer_policy                     = "no-referrer"
    }
    brute_force_detection {
      max_login_failures         = 5
      wait_increment_seconds     = 60
      max_failure_wait_seconds   = 900
      failure_reset_time_seconds = 900
    }
  }
}

# Broker to the corporate directory (Entra ID in production). Signature
# validation against the JWKS, no trusted e-mail, attributes re-synchronised
# at every login so that leaving the corporate group removes the role.
resource "keycloak_oidc_identity_provider" "corporate" {
  realm             = keycloak_realm.platform.id
  alias             = "corporate"
  display_name      = "Corporate login"
  authorization_url = "${var.public_url}/realms/corporate/protocol/openid-connect/auth"
  token_url         = "${var.public_url}/realms/corporate/protocol/openid-connect/token"
  jwks_url          = "${var.public_url}/realms/corporate/protocol/openid-connect/certs"
  issuer            = "${var.public_url}/realms/corporate"
  client_id         = keycloak_openid_client.platform_broker.client_id

  client_secret_wo         = var.broker_secret
  client_secret_wo_version = tostring(var.broker_secret_version)

  validate_signature = true
  trust_email        = false
  sync_mode          = "FORCE"
  default_scopes     = "openid profile email"
  extra_config = {
    "pkceEnabled" = "true"
    "pkceMethod"  = "S256"
  }
}

resource "keycloak_role" "case_worker" {
  realm_id        = keycloak_realm.platform.id
  name            = "case-worker"
  description     = "Granted by membership in the corporate group sachbearbeitung"
  composite_roles = [keycloak_role.benefits_read.id]
}

resource "keycloak_attribute_to_role_identity_provider_mapper" "case_worker" {
  realm                   = keycloak_realm.platform.id
  name                    = "sachbearbeitung-to-case-worker"
  identity_provider_alias = keycloak_oidc_identity_provider.corporate.alias
  claim_name              = "groups"
  claim_value             = "/sachbearbeitung"
  role                    = keycloak_role.case_worker.name
  extra_config = {
    syncMode = "FORCE"
  }
}
