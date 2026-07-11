# 1. Create the dedicated Security Namespace
resource "kubernetes_namespace_v1" "security" {
  metadata {
    name = "security"
  }
}

# 2. Deploy HashiCorp Vault via the Official Helm Chart
resource "helm_release" "vault" {
  name       = "vault"
  repository = "https://helm.releases.hashicorp.com"
  chart      = "vault"
  namespace  = kubernetes_namespace_v1.security.metadata[0].name
  version    = "0.28.0"

  # Refactored: Using YAML values instead of multiple 'set' blocks
  values = [
    <<-EOT
    server:
      dev:
        enabled: true
        # We removed devRootToken completely so it defaults to "root"
      resources:
        requests:
          memory: "256Mi"
        limits:
          memory: "512Mi"
    injector:
      enabled: true
    EOT
  ]
}

# 3. Configure the Vault Provider to talk to our new instance
provider "vault" {
  address = "http://127.0.0.1:8200"
  token   = "root" # <-- Changed to the absolute default
}

# 4. Enable Kubernetes Auth Method inside Vault
resource "vault_auth_backend" "kubernetes" {
  type       = "kubernetes"
  path       = "kubernetes"
  depends_on = [helm_release.vault]
}

# 5. Configure Vault to validate K8s Service Account tokens
resource "vault_kubernetes_auth_backend_config" "k8s_config" {
  backend                = vault_auth_backend.kubernetes.path
  kubernetes_host        = "https://kubernetes.default.svc.cluster.local:443"
  disable_iss_validation = true 
}

# 6. Create a Policy allowing access to our agent secrets
resource "vault_policy" "agent_policy" {
  name   = "langgraph-policy"
  policy = <<EOT
path "secret/data/agent-factory/*" {
  capabilities = ["read"]
}
EOT
}

# 7. Map the Kubernetes Service Account to the Vault Policy
resource "vault_kubernetes_auth_backend_role" "agent_role" {
  backend                          = vault_auth_backend.kubernetes.path
  role_name                        = "langgraph-auth-role"
  bound_service_account_names      = ["langgraph-sa"]
  bound_service_account_namespaces = ["agent-factory"]
  token_policies                   = [vault_policy.agent_policy.name]
  token_ttl                        = 3600
}

# 8. Pre-seed our Dummy API Key into Vault
resource "vault_generic_secret" "dummy_api_key" {
  path = "secret/data/agent-factory/keys"

  data_json = jsonencode({
    api_key = "sk-local-factory-dummy-12345"
  })

  depends_on = [helm_release.vault]
}

# 9. Deploy Official Keycloak in pure "Dev Mode" (In-Memory Database)
resource "kubernetes_deployment" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = kubernetes_namespace_v1.security.metadata[0].name
  }

  # ADDED: Tell Terraform to patiently wait up to 15 minutes for the K8s rollout
  timeouts {
    create = "15m"
    update = "15m"
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "keycloak"
      }
    }

    template {
      metadata {
        labels = {
          app = "keycloak"
        }
      }

      spec {
        container {
          name  = "keycloak"
          image = "quay.io/keycloak/keycloak:22.0.5"
          args  = ["start-dev"]

          env {
            name  = "KEYCLOAK_ADMIN"
            value = "admin"
          }
          env {
            name  = "KEYCLOAK_ADMIN_PASSWORD"
            value = "keycloak-admin-password-local"
          }

          port {
            container_port = 8080
          }

          resources {
            # BUMPED: Java is hungry. Let's give it 2GB of RAM to boot safely.
            limits = {
              memory = "2Gi" 
              cpu    = "1000m"
            }
            requests = {
              memory = "1Gi"
              cpu    = "500m"
            }
          }
        }
      }
    }
  }
}

# 10. Expose the Keycloak pod to the cluster internal network
resource "kubernetes_service" "keycloak" {
  metadata {
    name      = "keycloak"
    namespace = kubernetes_namespace_v1.security.metadata[0].name
  }
  spec {
    selector = {
      app = "keycloak"
    }
    port {
      port        = 8080
      target_port = 8080
    }
    type = "ClusterIP"
  }
}