# Simulated corporate directory. In production this is Microsoft Entra ID, a
# managed service that is not open source and is not part of the lab; the
# platform realm brokers to it with the same OIDC contract (authorization,
# token and JWKS endpoints, issuer, groups claim). Only the URLs change.

resource "keycloak_realm" "corporate" {
  realm        = "corporate"
  enabled      = true
  display_name = "Corporate directory (simulated Entra ID)"
  ssl_required = "external"

  access_token_lifespan   = "5m"
  revoke_refresh_token    = true
  refresh_token_max_reuse = 0

  # Two factors at the corporate login (BAS guide: two-factor minimum).
  otp_policy {
    type      = "totp"
    algorithm = "HmacSHA256"
    digits    = 6
    period    = 30
  }

  security_defenses {
    brute_force_detection {
      max_login_failures         = 5
      wait_increment_seconds     = 60
      max_failure_wait_seconds   = 900
      failure_reset_time_seconds = 900
    }
  }
}

resource "keycloak_required_action" "corporate_totp" {
  realm_id       = keycloak_realm.corporate.id
  alias          = "CONFIGURE_TOTP"
  enabled        = true
  default_action = true
}

resource "keycloak_group" "case_workers" {
  realm_id = keycloak_realm.corporate.id
  name     = "sachbearbeitung"
}

resource "keycloak_user" "anna" {
  realm_id       = keycloak_realm.corporate.id
  username       = "anna"
  email          = "anna@corporate.localtest.me"
  email_verified = true
  first_name     = "Anna"
  last_name      = "Demo"

  # Write-only: the password is sent to Keycloak but kept out of plan and state.
  initial_password {
    value_wo         = var.demo_user_password
    value_wo_version = "1"
    temporary        = true
  }
  required_actions = ["CONFIGURE_TOTP"]
}

resource "keycloak_group_memberships" "case_workers" {
  realm_id = keycloak_realm.corporate.id
  group_id = keycloak_group.case_workers.id
  members  = [keycloak_user.anna.username]
}

# The client the platform realm uses to broker logins. The one place where a
# shared secret remains (Entra ID app registrations work the same way unless
# a certificate or federated credential is configured).
resource "keycloak_openid_client" "platform_broker" {
  realm_id                     = keycloak_realm.corporate.id
  client_id                    = "platform-broker"
  name                         = "Identity platform broker"
  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = true
  implicit_flow_enabled        = false
  direct_access_grants_enabled = false
  full_scope_allowed           = false
  pkce_code_challenge_method   = "S256"
  valid_redirect_uris          = ["${var.public_url}/realms/platform/broker/corporate/endpoint"]

  client_secret_wo         = var.broker_secret
  client_secret_wo_version = tostring(var.broker_secret_version)
}

resource "keycloak_openid_group_membership_protocol_mapper" "broker_groups" {
  realm_id   = keycloak_realm.corporate.id
  client_id  = keycloak_openid_client.platform_broker.id
  name       = "groups"
  claim_name = "groups"
  full_path  = true
}
