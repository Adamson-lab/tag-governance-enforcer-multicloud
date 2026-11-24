terraform {

  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.60" }
  }

}

variable "name_prefix" {
  type = string
  default = "tag-enforcer"
}
variable "tags"        {
  type = map(string)
}
variable "lambda_zip"  {
  type = string
  description = "Path to packaged src/tagenforcer + handler"
}
variable "org_id"      {
  type = string
  description = "AWS Organizations ID (placeholder in examples)"
}

resource "aws_kms_key" "this" {
  description = "${var.name_prefix} CMK"
  enable_key_rotation = true
  tags = var.tags
}

resource "aws_dynamodb_table" "findings" {

  name = "${var.name_prefix}-findings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "resource_id"
  range_key = "evaluated_at"
  attribute {
    name = "resource_id"
    type = "S"
  }
  attribute {
    name = "evaluated_at"
    type = "S"
  }
  point_in_time_recovery {
    enabled = true
  }
  server_side_encryption {
    enabled = true
    kms_key_arn = aws_kms_key.this.arn
  }
  tags = var.tags

}

resource "aws_sqs_queue" "dlq"    {
  name = "${var.name_prefix}-dlq"
  kms_master_key_id = aws_kms_key.this.id
  tags = var.tags
}
resource "aws_sqs_queue" "ingest" {

  name = "${var.name_prefix}-ingest"
  kms_master_key_id = aws_kms_key.this.id
  visibility_timeout_seconds = 180
  redrive_policy = jsonencode({ deadLetterTargetArn = aws_sqs_queue.dlq.arn, maxReceiveCount = 5 })
  tags = var.tags

}
resource "aws_sns_topic" "escalate" {
  name = "${var.name_prefix}-escalate"
  kms_master_key_id = aws_kms_key.this.id
  tags = var.tags
}

data "aws_iam_policy_document" "assume" {

  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }

}
resource "aws_iam_role" "evaluator" {
  name = "${var.name_prefix}-evaluator"
  assume_role_policy = data.aws_iam_policy_document.assume.json
  tags = var.tags
}

data "aws_iam_policy_document" "evaluator" {

  statement {
    actions = ["dynamodb:PutItem", "dynamodb:Query"]
    resources = [aws_dynamodb_table.findings.arn]
  }
  statement {
    actions = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [aws_sqs_queue.ingest.arn]
  }
  statement {
    actions = ["sns:Publish"]
    resources = [aws_sns_topic.escalate.arn]
  }
  statement {
    actions = ["tag:GetResources"]
    resources = ["*"]
  }
  statement {
    actions = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["*"]
  }
  # Cross-account tag writes happen only via the separate TagWriter role in each member account (tag APIs only).

}
resource "aws_iam_role_policy" "evaluator" {
  role = aws_iam_role.evaluator.id
  policy = data.aws_iam_policy_document.evaluator.json
}

resource "aws_lambda_function" "evaluator" {

  function_name = "${var.name_prefix}-evaluator"
  role = aws_iam_role.evaluator.arn
  runtime = "python3.12"
  handler = "tagenforcer.handler.aws_handler"
  filename = var.lambda_zip
  source_code_hash = filebase64sha256(var.lambda_zip)
  timeout = 60
  memory_size = 512
  reserved_concurrent_executions = 50
  environment {
    variables = { STANDARD_PATH = "policies/tag-standard.json", TABLE = aws_dynamodb_table.findings.name, ESCALATE_TOPIC = aws_sns_topic.escalate.arn }
  }
  tags = var.tags

}
resource "aws_lambda_event_source_mapping" "ingest" {
  event_source_arn = aws_sqs_queue.ingest.arn
  function_name = aws_lambda_function.evaluator.arn
  batch_size = 10
}

resource "aws_cloudwatch_event_bus" "central" {
  name = "${var.name_prefix}-bus"
  tags = var.tags
}
resource "aws_cloudwatch_event_rule" "tag_change" {

  name = "${var.name_prefix}-tag-change"
  event_bus_name = aws_cloudwatch_event_bus.central.name
  event_pattern = jsonencode({ source = ["aws.tag", "aws.config"], "detail-type" = ["Tag Change on Resource", "Config Rules Compliance Change"] })

}
resource "aws_cloudwatch_event_target" "to_queue" {
  rule = aws_cloudwatch_event_rule.tag_change.name
  event_bus_name = aws_cloudwatch_event_bus.central.name
  arn = aws_sqs_queue.ingest.arn
}

# Preventive layer: organization tag policy and SCP (attach to OUs from the management account)
resource "aws_organizations_policy" "tag_policy" {
  name = "tag-standard-v1"
  type = "TAG_POLICY"
  content = file("${path.module}/../../../policies/aws/tag-policy.json")
}
resource "aws_organizations_policy" "scp_deny_untagged" {
  name = "deny-untagged-create"
  type = "SERVICE_CONTROL_POLICY"
  content = file("${path.module}/../../../policies/aws/scp-deny-untagged-create.json")
}

resource "aws_cloudwatch_metric_alarm" "dlq_depth" {

  alarm_name = "${var.name_prefix}-dlq-not-empty"
  namespace = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  dimensions = { QueueName = aws_sqs_queue.dlq.name }
  statistic = "Maximum"
  period = 300
  evaluation_periods = 1
  threshold = 0
  comparison_operator = "GreaterThanThreshold"
  alarm_actions = [aws_sns_topic.escalate.arn]

}
output "bus_arn" {
  value = aws_cloudwatch_event_bus.central.arn
}
output "findings_table" {
  value = aws_dynamodb_table.findings.name
}
