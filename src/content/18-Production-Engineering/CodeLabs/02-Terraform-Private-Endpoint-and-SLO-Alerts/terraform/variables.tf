variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "app_name" {
  type    = string
  default = "rag-api"
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "Use at least two private subnets (two availability zones) for the endpoint."
  }
}

variable "model_ids" {
  description = "Approved Bedrock model ids - exact ids only, no wildcards."
  type        = list(string)
  validation {
    condition     = length(var.model_ids) > 0 && alltrue([for id in var.model_ids : !strcontains(id, "*")])
    error_message = "List approved model ids explicitly; wildcards are not allowed."
  }
}

variable "cluster_name" {
  type = string
}

variable "namespace" {
  type    = string
  default = "rag"
}

variable "service_account" {
  type    = string
  default = "rag-api"
}
