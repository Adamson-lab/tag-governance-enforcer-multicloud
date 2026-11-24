terraform {

  required_version = ">= 1.6"
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.110" }
  }

}
variable "management_group_id" {
  type = string
}
variable "required_tags" {
  type = list(string)
  default = ["owner", "cost-center", "environment", "application", "data-classification", "compliance-scope", "managed-by"]
}
variable "effect" {
  type = string
  default = "Audit"
  description = "Audit first, then Deny (see rollout wave 3)"
}
variable "location" {
  type = string
  default = "eastus"
}

resource "azurerm_policy_definition" "require_tag" {

  name = "require-tag-v1"
  policy_type = "Custom"
  mode = "Indexed"
  display_name = "Require tag (Tag Standard v1)"
  management_group_id = var.management_group_id
  policy_rule = jsonencode(jsondecode(file("${path.module}/../../../policies/azure/require-tag.json")).properties.policyRule)
  parameters  = jsonencode(jsondecode(file("${path.module}/../../../policies/azure/require-tag.json")).properties.parameters)

}
resource "azurerm_policy_definition" "inherit_tag" {

  name = "inherit-tag-from-rg-v1"
  policy_type = "Custom"
  mode = "Indexed"
  display_name = "Inherit tag from RG (Tag Standard v1)"
  management_group_id = var.management_group_id
  policy_rule = jsonencode(jsondecode(file("${path.module}/../../../policies/azure/inherit-tag-from-rg.json")).properties.policyRule)
  parameters  = jsonencode(jsondecode(file("${path.module}/../../../policies/azure/inherit-tag-from-rg.json")).properties.parameters)

}
resource "azurerm_management_group_policy_assignment" "require" {

  for_each = toset(var.required_tags)
  name = substr("req-${each.key}", 0, 24)
  management_group_id = var.management_group_id
  policy_definition_id = azurerm_policy_definition.require_tag.id
  parameters = jsonencode({ tagName = { value = each.key }, effect = { value = var.effect } })

}
resource "azurerm_management_group_policy_assignment" "inherit" {

  for_each = toset(["owner", "cost-center", "environment", "application"])
  name = substr("inh-${each.key}", 0, 24)
  management_group_id = var.management_group_id
  policy_definition_id = azurerm_policy_definition.inherit_tag.id
  location = var.location
  identity {
    type = "SystemAssigned"
  }
  parameters = jsonencode({ tagName = { value = each.key } })

}
# Modify needs the assignment identity to hold Tag Contributor at the management group.
resource "azurerm_role_assignment" "inherit_tag_contributor" {

  for_each = azurerm_management_group_policy_assignment.inherit
  scope = var.management_group_id
  role_definition_name = "Tag Contributor"
  principal_id = each.value.identity[0].principal_id

}
