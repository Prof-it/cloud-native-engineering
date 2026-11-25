output "platform_issuer" {
  description = "Issuer the APIs compare exactly (tokencheck policy 'issuer')."
  value       = "${var.public_url}/realms/${keycloak_realm.platform.realm}"
}

output "token_endpoint" {
  value = "${var.public_url}/realms/${keycloak_realm.platform.realm}/protocol/openid-connect/token"
}

output "jwks_uri" {
  value = "${var.public_url}/realms/${keycloak_realm.platform.realm}/protocol/openid-connect/certs"
}

output "worker_subject" {
  description = "Service-account subject the claims-worker client accepts."
  value       = keycloak_openid_client.claims_worker.extra_config["jwt.credential.sub"]
}
