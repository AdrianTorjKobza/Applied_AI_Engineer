# observability.tf

resource "kubernetes_namespace_v1" "observability" {
  metadata {
    name = "observability"
  }
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "prometheus-stack"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  namespace  = kubernetes_namespace_v1.observability.metadata[0].name
  version    = "58.2.1" 

  # 1. Give Docker Desktop 10 minutes to pull images (default is 5)
  timeout = 600

  # 2. Disable admission webhooks to bypass the "pre-install" timeout bug
  set {
    name  = "prometheusOperator.admissionWebhooks.enabled"
    value = "false"
  }
  set {
    name  = "prometheusOperator.tls.enabled"
    value = "false"
  }

  # 3. Disable Alertmanager to save your RAM
  set {
    name  = "alertmanager.enabled"
    value = "false"
  }

  # 4. Set a simple Grafana password
  set {
    name  = "grafana.adminPassword"
    value = "sre-admin-password"
  }
}