# Clients of the platform realm. Each one gets exactly what it needs:
# full_scope_allowed = false everywhere, so a token carries only the roles
# that are mapped into the client's scope (G11).

# --- Resource servers -------------------------------------------------------

resource "keycloak_openid_client" "benefits_api" {
  realm_id                     = keycloak_realm.platform.id
  client_id                    = "benefits-api"
  name                         = "Benefits API"
  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = false
  implicit_flow_enabled        = false
  direct_access_grants_enabled = false
  service_accounts_enabled     = true
  full_scope_allowed           = false

  # Calls the documents API on behalf of the caller (standard token exchange,
  # RFC 8693, Keycloak 26.2+). Authenticates with its pod's service-account token.
  standard_token_exchange_enabled = true
  client_authenticator_type       = "federated-jwt"
  extra_config = {
    "jwt.credential.issuer" = keycloak_kubernetes_identity_provider.cluster.alias
    "jwt.credential.sub"    = "system:serviceaccount:${var.workload_namespace}:benefits-api"
  }
}

resource "keycloak_role" "benefits_read" {
  realm_id  = keycloak_realm.platform.id
  client_id = keycloak_openid_client.benefits_api.id
  name      = "benefits:read"
}

resource "keycloak_openid_client" "documents_api" {
  realm_id                     = keycloak_realm.platform.id
  client_id                    = "documents-api"
  name                         = "Documents API"
  access_type                  = "BEARER-ONLY"
  standard_flow_enabled        = false
  implicit_flow_enabled        = false
  direct_access_grants_enabled = false
  full_scope_allowed           = false
}

resource "keycloak_role" "documents_read" {
  realm_id  = keycloak_realm.platform.id
  client_id = keycloak_openid_client.documents_api.id
  name      = "documents:read"
}

# --- Audience scopes (I6: the audience is explicit, never "any API") --------

resource "keycloak_openid_client_scope" "aud_benefits" {
  realm_id               = keycloak_realm.platform.id
  name                   = "aud-benefits-api"
  include_in_token_scope = false
}

resource "keycloak_openid_audience_protocol_mapper" "aud_benefits" {
  realm_id                 = keycloak_realm.platform.id
  client_scope_id          = keycloak_openid_client_scope.aud_benefits.id
  name                     = "audience-benefits-api"
  included_client_audience = keycloak_openid_client.benefits_api.client_id
  add_to_access_token      = true
  add_to_id_token          = false
}

resource "keycloak_openid_client_scope" "aud_documents" {
  realm_id               = keycloak_realm.platform.id
  name                   = "aud-documents-api"
  include_in_token_scope = false
}

resource "keycloak_openid_audience_protocol_mapper" "aud_documents" {
  realm_id                 = keycloak_realm.platform.id
  client_scope_id          = keycloak_openid_client_scope.aud_documents.id
  name                     = "audience-documents-api"
  included_client_audience = keycloak_openid_client.documents_api.client_id
  add_to_access_token      = true
  add_to_id_token          = false
}

# --- Portal: a single-page app, public client with PKCE ---------------------

resource "keycloak_openid_client" "portal_web" {
  realm_id                     = keycloak_realm.platform.id
  client_id                    = "portal-web"
  name                         = "Case worker portal"
  access_type                  = "PUBLIC"
  standard_flow_enabled        = true
  implicit_flow_enabled        = false
  direct_access_grants_enabled = false
  full_scope_allowed           = false
  pkce_code_challenge_method   = "S256"
  valid_redirect_uris          = var.portal_redirect_uris
  web_origins                  = ["+"]
  access_token_lifespan        = "300"
}

resource "keycloak_openid_client_default_scopes" "portal_web" {
  realm_id       = keycloak_realm.platform.id
  client_id      = keycloak_openid_client.portal_web.id
  default_scopes = ["basic", "profile", "email", "roles", "web-origins", keycloak_openid_client_scope.aud_benefits.name]
}

resource "keycloak_generic_role_mapper" "portal_benefits_read" {
  realm_id  = keycloak_realm.platform.id
  client_id = keycloak_openid_client.portal_web.id
  role_id   = keycloak_role.benefits_read.id
}

# --- Batch worker: machine identity from its Kubernetes service account -----

resource "keycloak_openid_client" "claims_worker" {
  realm_id                     = keycloak_realm.platform.id
  client_id                    = "claims-worker"
  name                         = "Claims batch worker"
  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = false
  implicit_flow_enabled        = false
  direct_access_grants_enabled = false
  service_accounts_enabled     = true
  full_scope_allowed           = false
  access_token_lifespan        = "300"

  # No secret anywhere: the client authenticates with the projected
  # service-account token of its pod (RFC 7523 client assertion).
  client_authenticator_type = "federated-jwt"
  extra_config = {
    "jwt.credential.issuer" = keycloak_kubernetes_identity_provider.cluster.alias
    "jwt.credential.sub"    = "system:serviceaccount:${var.workload_namespace}:claims-worker"
  }
}

resource "keycloak_openid_client_default_scopes" "claims_worker" {
  realm_id       = keycloak_realm.platform.id
  client_id      = keycloak_openid_client.claims_worker.id
  default_scopes = ["basic", "roles", keycloak_openid_client_scope.aud_benefits.name]
}

# The worker's service account holds benefits:read and documents:read ...
resource "keycloak_openid_client_service_account_role" "worker_benefits_read" {
  realm_id                = keycloak_realm.platform.id
  service_account_user_id = keycloak_openid_client.claims_worker.service_account_user_id
  client_id               = keycloak_openid_client.benefits_api.id
  role                    = keycloak_role.benefits_read.name
}

resource "keycloak_openid_client_service_account_role" "worker_documents_read" {
  realm_id                = keycloak_realm.platform.id
  service_account_user_id = keycloak_openid_client.claims_worker.service_account_user_id
  client_id               = keycloak_openid_client.documents_api.id
  role                    = keycloak_role.documents_read.name
}

# ... but only benefits:read is in the worker's own scope. documents:read
# reaches a token only through the benefits API's token exchange, whose scope
# contains it: the worker cannot call the documents API directly.
resource "keycloak_generic_role_mapper" "worker_benefits_read" {
  realm_id  = keycloak_realm.platform.id
  client_id = keycloak_openid_client.claims_worker.id
  role_id   = keycloak_role.benefits_read.id
}

resource "keycloak_openid_client_default_scopes" "benefits_api" {
  realm_id       = keycloak_realm.platform.id
  client_id      = keycloak_openid_client.benefits_api.id
  default_scopes = ["basic", "roles", keycloak_openid_client_scope.aud_documents.name]
}

resource "keycloak_generic_role_mapper" "benefits_documents_read" {
  realm_id  = keycloak_realm.platform.id
  client_id = keycloak_openid_client.benefits_api.id
  role_id   = keycloak_role.documents_read.id
}
