# Runs offline: `tofu test` with a mocked AWS provider - no account or credentials needed.
mock_provider "aws" {
  # Mocked computed values must still be valid where the provider validates them (ARNs, ids).
  mock_resource "aws_iam_role" {
    defaults = { arn = "arn:aws:iam::123456789012:role/rag-api-model-invoker" }
  }
  mock_resource "aws_vpc_endpoint" {
    defaults = { id = "vpce-0abc123def4567890" }
  }
  mock_resource "aws_security_group" {
    defaults = { id = "sg-0abc123def4567890" }
  }
}

variables {
  vpc_id             = "vpc-0123456789abcdef0"
  private_subnet_ids = ["subnet-aaaa1111", "subnet-bbbb2222"]
  model_ids          = ["amazon.nova-pro-v1:0"]
  cluster_name       = "prod"
}

run "endpoint_is_private_and_scoped" {
  command = apply

  assert {
    condition     = aws_vpc_endpoint.bedrock_runtime.private_dns_enabled
    error_message = "Private DNS must be on so the SDK hostname resolves to the endpoint."
  }

  assert {
    condition     = aws_vpc_endpoint.bedrock_runtime.service_name == "com.amazonaws.eu-west-1.bedrock-runtime"
    error_message = "Wrong endpoint service."
  }

  assert {
    condition = toset(jsondecode(aws_vpc_endpoint.bedrock_runtime.policy).Statement[0].Action) == toset([
      "bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"
    ])
    error_message = "The endpoint policy must allow model invocation only."
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.endpoint_from_app.from_port == 443 && aws_vpc_security_group_ingress_rule.endpoint_from_app.referenced_security_group_id == aws_security_group.app.id
    error_message = "Only the app security group may reach the endpoint, on 443."
  }
}

run "role_requires_the_endpoint" {
  command = apply

  assert {
    condition     = jsondecode(aws_iam_role_policy.invoke.policy).Statement[0].Condition.StringEquals["aws:SourceVpce"] == aws_vpc_endpoint.bedrock_runtime.id
    error_message = "Model calls must be conditioned on the VPC endpoint."
  }

  assert {
    condition     = jsondecode(aws_iam_role_policy.invoke.policy).Statement[0].Resource == ["arn:aws:bedrock:eu-west-1::foundation-model/amazon.nova-pro-v1:0"]
    error_message = "The role must be scoped to the approved model ARNs."
  }
}

run "rejects_wildcard_models" {
  command = plan
  variables {
    model_ids = ["anthropic.*"]
  }
  expect_failures = [var.model_ids]
}

run "rejects_single_subnet" {
  command = plan
  variables {
    private_subnet_ids = ["subnet-aaaa1111"]
  }
  expect_failures = [var.private_subnet_ids]
}
