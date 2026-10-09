output "endpoint_id" {
  value = aws_vpc_endpoint.bedrock_runtime.id
}

output "workload_role_arn" {
  value = aws_iam_role.workload.arn
}

output "app_security_group_id" {
  description = "Attach this to the workload's pods or nodes so they can reach the endpoint."
  value       = aws_security_group.app.id
}
