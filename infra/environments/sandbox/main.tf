# Sandbox composition. Replace placeholders; never commit real IDs. Apply per cloud with its own backend and OIDC role.
locals {
  tags = { owner = "team-ccoe", "cost-center" = "cc-90001", environment = "sandbox", application = "tag-enforcer", "data-classification" = "internal", "compliance-scope" = "none", "managed-by" = "terraform", expiry = "2027-03-31" }
}
module "aws" {
  source = "../../modules/aws"
  name_prefix = "tag-enforcer-sbx"
  tags = local.tags
  lambda_zip = "../../../dist/enforcer.zip"
  org_id = "o-xxxxxxxxxx"
}
# module "azure" { source = "../../modules/azure", management_group_id = "/providers/Microsoft.Management/managementGroups/mg-sandbox" }
# module "gcp"   { source = "../../modules/gcp", org_id = "000000000000", project_id = "tag-enforcer-gov-sbx" }
