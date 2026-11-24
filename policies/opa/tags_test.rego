package tagging_test

import rego.v1

import data.tagging

full := {"owner": "team-a", "cost-center": "cc-10001", "environment": "dev", "application": "app-one", "data-classification": "internal", "compliance-scope": "none", "managed-by": "terraform"}

test_compliant_plan_has_no_denials if {
	count(tagging.deny) == 0 with input as {"resource_changes": [{"address": "aws_s3_bucket.a", "type": "aws_s3_bucket", "change": {"actions": ["create"], "after": {"tags_all": full}}}]}
}

test_missing_tag_denied if {
	t := object.remove(full, ["cost-center"])
	count(tagging.deny) == 1 with input as {"resource_changes": [{"address": "aws_s3_bucket.a", "type": "aws_s3_bucket", "change": {"actions": ["create"], "after": {"tags_all": t}}}]}
}

test_bad_gcp_label_key_denied if {
	l := object.union(full, {"Bad Key": "x"})
	count(tagging.deny) == 1 with input as {"resource_changes": [{"address": "google_storage_bucket.b", "type": "google_storage_bucket", "change": {"actions": ["create"], "after": {"labels": l}}}]}
}
