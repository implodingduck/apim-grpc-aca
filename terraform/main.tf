terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.109.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "=3.1.0"
    }
    azapi = {
      source = "azure/azapi"
      version = "=1.13.1"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.53.1"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }

  subscription_id = var.subscription_id
}

resource "random_string" "unique" {
  length  = 8
  special = false
  upper   = false
}


data "azurerm_client_config" "current" {}

data "azurerm_log_analytics_workspace" "default" {
  name                = "DefaultWorkspace-${data.azurerm_client_config.current.subscription_id}-EUS"
  resource_group_name = "DefaultResourceGroup-EUS"
} 

resource "azurerm_resource_group" "rg" {
  name     = "rg-${local.gh_repo}-${random_string.unique.result}-${local.loc_for_naming}"
  location = var.location
  tags = local.tags
}

resource "azurerm_user_assigned_identity" "this" {
  location            = azurerm_resource_group.rg.location
  name                = "uai-${local.cluster_name}"
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_key_vault" "kv" {
  name                       = "kv-${local.cluster_name}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false
  enable_rbac_authorization = true
}

resource "azurerm_role_assignment" "containerapptokv" {
  scope                = azurerm_key_vault.kv.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

resource "azurerm_role_assignment" "reader" {
  scope                = "/subscriptions/${data.azurerm_client_config.current.subscription_id}"
  role_definition_name = "Reader"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
}

resource "azurerm_container_app_environment" "this" {
  name                       = "ace-${local.cluster_name}"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  log_analytics_workspace_id = data.azurerm_log_analytics_workspace.default.id

  workload_profile {
    name                  = "Consumption"
    workload_profile_type = "Consumption"
  }

  tags = local.tags

}

resource "azurerm_container_app" "grpcbackend" {
  name                         = "grpcbackend"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  template {
    container {
      name   = "grpcbackend"
      image  = "ghcr.io/implodingduck/apim-grpc-aca-backend:latest"
      cpu    = 0.25
      memory = "0.5Gi"
      
    }
    http_scale_rule {
      name                = "http-1"
      concurrent_requests = "100"
    }
    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    target_port = 50051
    transport = "tcp"
    allow_insecure_connections = false
    external_enabled = false
    exposed_port = 50051
    
    traffic_weight {
      latest_revision = true
      percentage = 100
    }
    
  }

  identity {
    type = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.this.id]
  }
  tags = local.tags

  lifecycle {
    ignore_changes = [ secret ]
  }
}


resource "azurerm_container_app" "grpcclient" {
  name                         = "grpcclient"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  template {
    container {
      name   = "grpcclient"
      image  = "ghcr.io/implodingduck/apim-grpc-aca-client:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "GRPC_ENDPOINT"
        value = "${azurerm_container_app.grpcbackend.name}:50051"
      }
      
    }
    http_scale_rule {
      name                = "http-1"
      concurrent_requests = "100"
    }
    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 80
    transport                  = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  identity {
    type = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.this.id]
  }
  tags = local.tags

  lifecycle {
    ignore_changes = [ secret ]
  }
}

resource "azurerm_container_app" "grpcclientapim" {
  name                         = "grpcclientapim"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  template {
    container {
      name   = "grpcclient"
      image  = "ghcr.io/implodingduck/apim-grpc-aca-client:latest"
      cpu    = 0.25
      memory = "0.5Gi"

      env {
        name  = "GRPC_ENDPOINT"
        value = "${azurerm_container_app.apimgateway.name}:8080"
      }
      
    }
    http_scale_rule {
      name                = "http-1"
      concurrent_requests = "100"
    }
    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 80
    transport                  = "auto"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }

  identity {
    type = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.this.id]
  }
  tags = local.tags

  lifecycle {
    ignore_changes = [ secret ]
  }
}

resource "azurerm_container_app" "apimgateway" {
  name                         = "grpcapimgateway"
  container_app_environment_id = azurerm_container_app_environment.this.id
  resource_group_name          = azurerm_resource_group.rg.name
  revision_mode                = "Single"
  workload_profile_name        = "Consumption"

  template {
    container {
      name   = "apimgateway"
      #image  = "mcr.microsoft.com/azure-api-management/gateway:v2"
      image  = "mcr.microsoft.com/azure-api-management/gateway:2.7.1"
      cpu    = 0.25
      memory = "0.5Gi"

      # env {
      #   name  = "net.server.http.forwarded.proto.enabled"
      #   value = "true"
      # }
      env {
        name = "config.service.endpoint"
        secret_name = "config-service-endpoint"
      }
      
      env {
        name = "config.service.auth"
        secret_name = "config-service-token"
      }
    }
    http_scale_rule {
      name                = "http-1"
      concurrent_requests = "100"
    }
    min_replicas = 1
    max_replicas = 1
  }

  ingress {
    external_enabled           = false
    target_port                = 8080
    transport                  = "tcp"
    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
  
  secret {
    name = "config-service-endpoint"
    identity = azurerm_user_assigned_identity.this.id
    key_vault_secret_id = "${azurerm_key_vault.kv.vault_uri}secrets/CONFIG-SERVICE-ENDPOINT"
  }

  secret {
    name = "config-service-token"
    identity = azurerm_user_assigned_identity.this.id
    key_vault_secret_id = "${azurerm_key_vault.kv.vault_uri}secrets/CONFIG-SERVICE-TOKEN"
  }


  identity {
    type = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.this.id]
  }
  tags = local.tags

  lifecycle {
    ignore_changes = [ secret ]
  }
}

resource "azurerm_application_insights" "app" {
  name                = "${local.cluster_name}-insights"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  application_type    = "other"
  workspace_id        = data.azurerm_log_analytics_workspace.default.id
}