package tagging

import rego.v1

required := {"owner", "cost-center", "environment", "application", "data-classification", "compliance-scope", "managed-by"}

taggable := {"aws_instance", "aws_s3_bucket", "aws_db_instance", "aws_eks_cluster", "azurerm_resource_group", "azurerm_storage_account",
	"azurerm_linux_virtual_machine", "google_compute_instance", "google_storage_bucket", "google_bigquery_dataset"}

resource_tags(r) := t if {
	t := r.change.after.tags_all
} else := t if {
	t := r.change.after.tags
} else := t if {
	t := r.change.after.labels
} else := {}

deny contains msg if {
	some r in input.resource_changes
	r.type in taggable
	some a in r.change.actions
	a in {"create", "update"}
	some k in required
	not k in object.keys(resource_tags(r))
	msg := sprintf("%s: missing required tag/label '%s'", [r.address, k])
}

deny contains msg if {
	some r in input.resource_changes
	r.type in taggable
	startswith(r.type, "google_")
	some k, v in resource_tags(r)
	not regex.match(`^[a-z][a-z0-9_-]{0,62}$`, k)
	msg := sprintf("%s: '%s' is not a valid GCP label key", [r.address, k])
}
