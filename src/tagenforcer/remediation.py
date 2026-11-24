"""Turns an AUTO_FIX decision into provider-specific API call plans (no side effects here)."""
import re


def _gcp(s):
    return re.sub(r"[^a-z0-9_-]", "_", str(s).lower())[:63]


def to_cloud(cloud, tags):
    if cloud == "gcp":
        return {_gcp(k): _gcp(v) for k, v in tags.items()}
    return dict(tags)


def plan(result, resource):
    if result.action not in ("AUTO_FIX", "NOTIFY") or not (result.changes or result.remove_keys):
        return []
    c, tags, rm = result.cloud, to_cloud(result.cloud, result.changes), result.remove_keys
    if c == "aws":
        p = [{"api": "resourcegroupstaggingapi:TagResources", "arn": resource.id, "tags": tags}]
        if rm:
            p.append({"api": "resourcegroupstaggingapi:UntagResources", "arn": resource.id, "tag_keys": rm})
    elif c == "azure":
        p = [{"api": "Microsoft.Resources/tags", "operation": "Merge", "scope": resource.id, "tags": tags}]
        if rm:
            p.append({"api": "Microsoft.Resources/tags", "operation": "Delete", "scope": resource.id, "tags": {k: "" for k in rm}})
    elif c == "gcp":
        p = [{"api": "labels.update", "resource": resource.id, "labels": tags, "remove": [_gcp(k) for k in rm]}]
    else:
        raise ValueError(f"unknown cloud {c}")
    return p
