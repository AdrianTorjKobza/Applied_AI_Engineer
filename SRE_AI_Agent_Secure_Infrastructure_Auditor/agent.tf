# 1. Create the dedicated Service Account that Vault will authenticate
resource "kubernetes_service_account" "agent_sa" {
  metadata {
    name      = "langgraph-agent-sa"
    namespace = kubernetes_namespace_v1.security.metadata[0].name
  }
}

resource "kubernetes_deployment" "langgraph_agent" {
  metadata {
    name      = "langgraph-agent"
    namespace = kubernetes_namespace_v1.security.metadata[0].name
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = "langgraph-agent"
      }
    }

    template {
      metadata {
        labels = {
          app = "langgraph-agent"
        }
        # --- THE VAULT MAGIC ---
        annotations = {
          "vault.hashicorp.com/agent-inject" = "true"
          "vault.hashicorp.com/role"         = vault_kubernetes_auth_backend_role.agent_role.role_name
          
          # Tell Vault which secret to fetch from Phase 1
          "vault.hashicorp.com/agent-inject-secret-config.env" = "secret/data/agent-factory/config"
          
          # Format the secret as an export script so Python can read it as an OS Environment Variable
          "vault.hashicorp.com/agent-inject-template-config.env" = <<-EOT
            {{- with secret "secret/data/agent-factory/config" -}}
            export DUMMY_API_KEY="{{ .Data.data.DUMMY_API_KEY }}"
            {{- end -}}
          EOT
        }
      }

      spec {
        # The exact K8s Service Account we bound to Vault in Phase 1!
        service_account_name = kubernetes_service_account.agent_sa.metadata[0].name

        container {
          name              = "langgraph-agent"
          image             = "langgraph-agent:v1"
          image_pull_policy = "IfNotPresent"

          # The boot sequence override: Source the Vault secrets, then start FastAPI
          command = ["/bin/sh", "-c"]
          args    = ["source /vault/secrets/config.env && exec uvicorn main:app --host 0.0.0.0 --port 8000"]

          # Override our Python configuration to use Kubernetes internal routing
          env {
            name  = "KEYCLOAK_URL"
            value = "http://keycloak.security.svc.cluster.local:8080"
          }
          env {
            name  = "OLLAMA_BASE_URL"
            # Magic Docker Desktop DNS to access Ollama running on your Windows host!
            value = "http://host.docker.internal:11434" 
          }

          port {
            container_port = 8000
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "langgraph_agent" {
  metadata {
    name      = "langgraph-agent"
    namespace = kubernetes_namespace_v1.security.metadata[0].name
  }
  spec {
    selector = {
      app = "langgraph-agent"
    }
    port {
      port        = 8000
      target_port = 8000
    }
    type = "ClusterIP"
  }
}