# Workloads authenticate with their Kubernetes service-account token instead
# of a client secret (Keycloak 26.5+: Kubernetes identity provider and
# federated client authentication; enabled by default in current releases).
#
# Keycloak fetches <issuer>/.well-known/openid-configuration and the JWKS it
# names. kind: the API server, reached in-cluster with the cluster CA in the
# Keycloak truststore and anonymous discovery allowed
# (../30-issuer-discovery.yaml). AKS: the public OIDC issuer of the cluster.

resource "keycloak_kubernetes_identity_provider" "cluster" {
  realm  = keycloak_realm.platform.id
  alias  = "cluster"
  issuer = var.kubernetes_issuer
}

# Client authentication flow: a copy of the built-in "clients" flow plus the
# federated-jwt authenticator, so that clients using a secret or a signed JWT
# keep working. Binding a flow with federated-jwt alone would lock them out.
# No provider_id: with copy_from the copy keeps the type of its source
# ("client-flow"), and the provider rejects setting both.
resource "keycloak_authentication_flow" "clients_federated" {
  realm_id  = keycloak_realm.platform.id
  alias     = "clients-with-federated-jwt"
  copy_from = "clients"
}

resource "keycloak_authentication_execution" "federated_jwt" {
  realm_id          = keycloak_realm.platform.id
  parent_flow_alias = keycloak_authentication_flow.clients_federated.alias
  authenticator     = "federated-jwt"
  requirement       = "ALTERNATIVE"
}

resource "keycloak_authentication_bindings" "platform" {
  realm_id                   = keycloak_realm.platform.id
  client_authentication_flow = keycloak_authentication_flow.clients_federated.alias
  depends_on                 = [keycloak_authentication_execution.federated_jwt]
}
