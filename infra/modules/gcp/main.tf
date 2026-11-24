terraform {

  required_version = ">= 1.6"
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.40" }
  }

}
variable "org_id" {
  type = string
}
variable "project_id" {
  type = string
  description = "Governance project"
}
variable "region" {
  type = string
  default = "us-central1"
}

resource "google_pubsub_topic" "asset_feed" {
  project = var.project_id
  name = "tag-enforcer-asset-feed"
}
resource "google_pubsub_topic" "dlq"        {
  project = var.project_id
  name = "tag-enforcer-dlq"
}

resource "google_cloud_asset_organization_feed" "labels" {

  billing_project = var.project_id
  org_id = var.org_id
  feed_id = "tag-enforcer-feed"
  content_type = "RESOURCE"
  asset_types = ["compute.googleapis.com/Instance", "storage.googleapis.com/Bucket", "bigquery.googleapis.com/Dataset", "container.googleapis.com/Cluster"]
  feed_output_config {
    pubsub_destination {
      topic = google_pubsub_topic.asset_feed.id
    }
  }

}
resource "google_service_account" "evaluator" {
  project = var.project_id
  account_id = "tag-enforcer-eval"
}
resource "google_service_account" "writer"    {
  project = var.project_id
  account_id = "tag-enforcer-writer"
}

# Writer gets a custom role limited to label and tag-binding mutations; granted at org/folder level, never owner/editor.
resource "google_organization_iam_custom_role" "tag_writer" {

  org_id = var.org_id
  role_id = "tagEnforcerWriter"
  title = "Tag Enforcer Writer"
  permissions = ["resourcemanager.tagBindings.create", "resourcemanager.tagBindings.delete", "compute.instances.setLabels", "storage.buckets.update", "bigquery.datasets.update"]

}
resource "google_organization_iam_member" "writer" {
  org_id = var.org_id
  role = google_organization_iam_custom_role.tag_writer.name
  member = "serviceAccount:${google_service_account.writer.email}"
}

resource "google_firestore_database" "findings" {
  project = var.project_id
  name = "(default)"
  location_id = var.region
  type = "FIRESTORE_NATIVE"
}
resource "google_tags_tag_key" "cost_center" {
  parent = "organizations/${var.org_id}"
  short_name = "cost-center"
  description = "Tag Standard v1"
}
