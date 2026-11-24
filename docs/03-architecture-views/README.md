# Architecture views
Open `diagrams/index.html` for the gallery, or see `docs/diagram-index.md`. 20 diagrams, generated from code.
## Multicloud mapping table
| Capability | AWS | Azure | GCP | Abstraction chosen |
|---|---|---|---|---|
| Metadata key/value | Tags | Tags | Labels (+ Resource Manager tags) | canonical lowercase kebab-case |
| Prevent | SCP + Tag Policy | Policy Deny/Modify | Org Policy (limited) + CI gate | OPA gate + native deny where supported |
| Detect (events) | EventBridge + Config | Event Grid | Cloud Asset feed + Pub/Sub | adapters to neutral `Resource` |
| Detect (sweep) | Config / Tagging API | Resource Graph | Cloud Asset Inventory | nightly full sweep |
| Correct | TagResources | Tags merge | labels.update | `remediation.plan()` |
| Workflow | Step Functions | Logic Apps | Workflows | hub workflow (AWS) |
| Identity | IAM roles / OIDC | Managed identity / federated cred | WIF / SA impersonation | keyless everywhere |
