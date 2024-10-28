variable "subscription_id" {
  type = string
  sensitive = true
}


variable "location" {
  type    = string
  default = "East US"
}

variable "gh_repo" {
  type = string
}

variable "apimendpoint" {
  type = string
}