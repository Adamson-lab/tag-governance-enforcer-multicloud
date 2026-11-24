# Executive summary
**Problem.** Cloud spend and risk cannot be attributed to an owner when tags and labels are missing or inconsistent. Three clouds, three syntaxes (AWS tags, Azure tags, GCP labels) and three sets of limits make a single org-wide standard hard to enforce.
**Approach.** One versioned tag standard, one provider-neutral decision engine, and three thin cloud-native edges. Defence in layers: **prevent** (SCP/Tag Policy, Azure Policy, Org Policy, CI gate), **detect** (events plus nightly sweep), **correct** (auto-fix only deterministic changes; humans decide ownership).
**Outcome (targets, to be proven live).** Untagged spend from an assumed 22% to under 5%; every production resource has an accountable owner; audit evidence generated, not assembled by hand.
**Maturity.** Tier 3 prototype: engine and policies are tested locally (15 unit tests); IaC is written but not yet applied or `terraform validate`d in this package; cloud calls are not yet exercised against live accounts. See Known Limitations in the README.
**Ask.** Approve Wave 0 and Wave 1 (detect-only, read-only access) in one sandbox account per cloud.
