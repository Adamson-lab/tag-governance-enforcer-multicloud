"""Provider-neutral decision engine: one tag standard, three clouds.

Pure functions, no cloud SDK imports, so it runs identically inside AWS Lambda,
Azure Functions, Cloud Functions, CI and unit tests.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

CRITICAL_KEYS = {"owner", "cost-center", "data-classification"}
GCP_KEY = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
GCP_VAL = re.compile(r"^[a-z0-9_-]{0,63}$")


def load_standard(path=None) -> dict:
    p = Path(path) if path else Path(__file__).resolve().parents[2] / "policies" / "tag-standard.json"
    return json.loads(p.read_text(encoding="utf-8"))


@dataclass
class Resource:
    cloud: str
    id: str
    type: str = ""
    tags: dict = field(default_factory=dict)
    parent_tags: dict = field(default_factory=dict)
    account: str = ""


@dataclass
class Finding:
    rule: str
    severity: str
    key: str
    detail: str


@dataclass
class Result:
    resource_id: str
    cloud: str
    action: str
    findings: list
    proposed_tags: dict
    changes: dict
    remove_keys: list


def _known(std):
    return set(std["required"]) | {"expiry"}


def normalize(tags, std):
    """Canonicalise keys and values. Returns (clean, findings, renamed_original_keys)."""
    amap = {k.lower(): v for k, v in std["aliases"].items()}
    known = _known(std)
    prefixes = tuple(p.lower() for p in std["reserved_prefixes"])
    out, fs, renamed = {}, [], []
    for k, v in (tags or {}).items():
        if k.lower().startswith(prefixes):
            continue  # provider-owned system tags are never touched
        ck = amap.get(k.lower()) or (k.lower() if k.lower() in known else k)
        val = str(v).strip().lower() if ck in known else v
        if ck in out and out[ck] != val:
            fs.append(Finding("CONFLICT", "MEDIUM", ck, "duplicate keys with different values; human decision needed"))
            continue
        if ck != k:
            fs.append(Finding("KEY_DRIFT", "LOW", ck, f"'{k}' -> '{ck}'"))
            renamed.append(k)
        if ck in known and val != str(v):
            fs.append(Finding("VALUE_DRIFT", "LOW", ck, f"value normalised to '{val}'"))
        out[ck] = val
    return out, fs, renamed


def _ok(value, spec):
    if "enum" in spec and value not in spec["enum"]:
        return False
    if "pattern" in spec and re.fullmatch(spec["pattern"], str(value)) is None:
        return False
    return True


def _sev(key, env):
    if key in CRITICAL_KEYS:
        return "CRITICAL" if env == "prod" else "HIGH"
    return "MEDIUM"


def validate(tags, cloud, std, today):
    out, env = [], tags.get("environment")
    for k, spec in std["required"].items():
        if k not in tags:
            out.append(Finding("MISSING_REQUIRED", _sev(k, env), k, f"required tag '{k}' is missing"))
        elif not _ok(tags[k], spec):
            out.append(Finding("INVALID_VALUE", "MEDIUM", k, f"value '{tags[k]}' violates the '{k}' rule"))
    for cond in std["conditional"]:
        if all(tags.get(a) == b for a, b in cond["when"].items()):
            for k, spec in cond["require"].items():
                if k not in tags:
                    out.append(Finding("MISSING_REQUIRED", "HIGH", k, f"'{k}' required when {cond['when']}"))
                elif not _ok(tags[k], spec):
                    out.append(Finding("INVALID_VALUE", "MEDIUM", k, f"value '{tags[k]}' violates the '{k}' rule"))
    exp = tags.get("expiry")
    if exp and re.fullmatch(std["conditional"][0]["require"]["expiry"]["pattern"], exp):
        try:
            d = dt.date.fromisoformat(exp)
            if today > d + dt.timedelta(days=std["expiry_grace_days"]):
                out.append(Finding("EXPIRED", "HIGH", "expiry", f"expired {exp}, grace period over"))
            elif today > d:
                out.append(Finding("EXPIRING", "MEDIUM", "expiry", f"expired {exp}, inside grace period"))
        except ValueError:
            out.append(Finding("INVALID_VALUE", "MEDIUM", "expiry", f"'{exp}' is not a real date"))
    out += _limits(tags, cloud, std)
    return out


def _limits(tags, cloud, std):
    lim, fs = std["limits"][cloud], []
    if len(tags) > lim["max_tags"]:
        fs.append(Finding("LIMIT", "HIGH", "*", f"{len(tags)} tags exceeds {cloud} max {lim['max_tags']}"))
    for k, v in tags.items():
        if len(k) > lim["key_len"] or len(str(v)) > lim["val_len"]:
            fs.append(Finding("LIMIT", "HIGH", k, f"key/value length exceeds {cloud} limit"))
        if cloud == "gcp" and not (GCP_KEY.match(k) and GCP_VAL.match(str(v))):
            fs.append(Finding("LIMIT", "HIGH", k, "not a valid GCP label (lowercase, digits, _ and - only)"))
    return fs


def evaluate(res: Resource, std: dict, today=None, exemptions=None) -> Result:
    today = today or dt.date.today()
    clean, fs, renamed = normalize(res.tags, std)
    parent, _, _ = normalize(res.parent_tags, std)
    proposed = dict(clean)
    for k, spec in std["required"].items():
        if k not in proposed and spec.get("inheritable") and k in parent:
            proposed[k] = parent[k]
            fs.append(Finding("INHERITED", "LOW", k, f"inherited '{parent[k]}' from parent scope"))
    hard = validate(proposed, res.cloud, std, today)
    hard += [f for f in fs if f.rule == "CONFLICT"]  # conflicts always need a human
    fs += [f for f in hard if f.rule != "CONFLICT"]
    changes = {k: v for k, v in proposed.items() if res.tags.get(k) != v}

    if exemptions and res.id in exemptions and dt.date.fromisoformat(exemptions[res.id]) >= today:
        action = "EXEMPT"
    elif not fs:
        action = "COMPLIANT"
    elif any(f.rule == "EXPIRED" for f in hard):
        action = "EXPIRY_ENFORCE"
    elif any(f.rule != "EXPIRING" for f in hard):
        action = "ESCALATE" if any(f.severity == "CRITICAL" for f in hard) else "TICKET"
    elif hard:
        action = "NOTIFY"
    else:
        action = "AUTO_FIX"
    return Result(res.id, res.cloud, action, fs, proposed, changes, renamed)
