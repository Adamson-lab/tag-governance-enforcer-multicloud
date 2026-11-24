"""Map provider-native inventory records to the neutral Resource model."""
from .engine import Resource


def from_aws_config(item, parent_tags=None):
    return Resource("aws", item.get("ARN") or item["resourceId"], item.get("resourceType", ""),
                    dict(item.get("tags") or {}), dict(parent_tags or {}), item.get("awsAccountId", ""))


def from_azure_graph(row, parent_tags=None):
    return Resource("azure", row["id"], row.get("type", ""), dict(row.get("tags") or {}),
                    dict(parent_tags or {}), row.get("subscriptionId", ""))


def from_gcp_asset(asset, parent_labels=None):
    data = (asset.get("resource") or {}).get("data") or {}
    anc = asset.get("ancestors") or [""]
    return Resource("gcp", asset["name"], asset.get("assetType", ""), dict(data.get("labels") or {}),
                    dict(parent_labels or {}), anc[0])
