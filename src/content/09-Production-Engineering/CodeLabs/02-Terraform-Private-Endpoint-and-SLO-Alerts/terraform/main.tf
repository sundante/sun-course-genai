# Lab 09-02 - private, least-privilege access to a managed model (Amazon Bedrock) for one workload.
terraform {
  required_version = ">= 1.8"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

provider "aws" {
  region = var.region
}

locals {
  model_arns     = [for id in var.model_ids : "arn:aws:bedrock:${var.region}::foundation-model/${id}"]
  invoke_actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
  tags           = { app = var.app_name, managed_by = "opentofu" }
}

# --- network: only the app's security group can reach the endpoint, only on 443 --------------
resource "aws_security_group" "app" {
  name        = "${var.app_name}-app"
  description = "Workload calling the model"
  vpc_id      = var.vpc_id
  tags        = local.tags
}

resource "aws_security_group" "endpoint" {
  name        = "${var.app_name}-bedrock-endpoint"
  description = "Bedrock runtime interface endpoint"
  vpc_id      = var.vpc_id
  tags        = local.tags
}

resource "aws_vpc_security_group_ingress_rule" "endpoint_from_app" {
  security_group_id            = aws_security_group.endpoint.id
  referenced_security_group_id = aws_security_group.app.id
  ip_protocol                  = "tcp"
  from_port                    = 443
  to_port                      = 443
}

# --- private endpoint with a policy that allows only invoking the approved models ------------
resource "aws_vpc_endpoint" "bedrock_runtime" {
  vpc_id              = var.vpc_id
  service_name        = "com.amazonaws.${var.region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = var.private_subnet_ids
  security_group_ids  = [aws_security_group.endpoint.id]
  private_dns_enabled = true
  tags                = local.tags

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = "*"
      Action    = local.invoke_actions
      Resource  = local.model_arns
    }]
  })
}

# --- workload identity: EKS Pod Identity role, invoke-only, only through the endpoint --------
resource "aws_iam_role" "workload" {
  name = "${var.app_name}-model-invoker"
  tags = local.tags
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "pods.eks.amazonaws.com" }
      Action    = ["sts:AssumeRole", "sts:TagSession"]
    }]
  })
}

resource "aws_iam_role_policy" "invoke" {
  name = "invoke-approved-models"
  role = aws_iam_role.workload.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = local.invoke_actions
      Resource  = local.model_arns
      Condition = { StringEquals = { "aws:SourceVpce" = aws_vpc_endpoint.bedrock_runtime.id } }
    }]
  })
}

resource "aws_eks_pod_identity_association" "workload" {
  cluster_name    = var.cluster_name
  namespace       = var.namespace
  service_account = var.service_account
  role_arn        = aws_iam_role.workload.arn
}
