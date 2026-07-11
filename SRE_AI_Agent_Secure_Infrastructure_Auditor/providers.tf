terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11.0"
    }
    # ADDED: The Keycloak Provider
    keycloak = {
      source  = "mrparkers/keycloak"
      version = "~> 4.4.0"
    }
  }
  backend "local" {
    path = "./terraform.tfstate"
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "docker-desktop"
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "docker-desktop"
  }
}

# ADDED: Keycloak Provider Configuration
provider "keycloak" {
  client_id = "admin-cli"
  username  = "admin"
  password  = "keycloak-admin-password-local"
  url       = "http://127.0.0.1:8080"
}