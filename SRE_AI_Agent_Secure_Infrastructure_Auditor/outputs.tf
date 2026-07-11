output "keycloak_client_id" {
  description = "The OIDC Client ID for LangGraph"
  value       = keycloak_openid_client.langgraph_api.client_id
}

output "keycloak_client_secret" {
  description = "The auto-generated OIDC Client Secret"
  value       = keycloak_openid_client.langgraph_api.client_secret
  sensitive   = true
}

output "vault_agent_role" {
  description = "The Kubernetes Auth Role for Vault"
  value       = vault_kubernetes_auth_backend_role.agent_role.role_name
}