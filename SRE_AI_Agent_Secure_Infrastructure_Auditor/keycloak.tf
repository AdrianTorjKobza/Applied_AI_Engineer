# 1. Create the dedicated Realm for our project
resource "keycloak_realm" "agent_factory" {
  realm   = "agent-factory"
  enabled = true
}

# 2. Create the OIDC Client (The API bridge for LangGraph)
resource "keycloak_openid_client" "langgraph_api" {
  realm_id                     = keycloak_realm.agent_factory.id
  client_id                    = "langgraph-api"
  name                         = "LangGraph Agent Interface"
  enabled                      = true
  access_type                  = "CONFIDENTIAL"
  standard_flow_enabled        = true
  direct_access_grants_enabled = true
  valid_redirect_uris          = ["http://localhost:8000/*"]
}

# 3. Create the SRE Admin Role
resource "keycloak_role" "sre_admin" {
  realm_id = keycloak_realm.agent_factory.id
  name     = "SRE_Admin"
}

# 4. Create a Test Human User
resource "keycloak_user" "test_admin" {
  realm_id   = keycloak_realm.agent_factory.id
  username   = "admin-user"
  enabled    = true
  email      = "admin@agentfactory.local"
  first_name = "Agentic"
  last_name  = "Admin"
  
  initial_password {
    value     = "secure-password-123"
    temporary = false
  }
}

# 5. Bind the Role to the User
resource "keycloak_user_roles" "user_roles" {
  realm_id = keycloak_realm.agent_factory.id
  user_id  = keycloak_user.test_admin.id
  role_ids = [
    keycloak_role.sre_admin.id
  ]
}