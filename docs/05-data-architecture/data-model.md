# Data architecture
Conceptual: Resource (cloud, id, type, account) has Tags; Finding references Resource and Rule; Waiver references Resource; Standard has version.
| Entity | Store | Key | Retention | Classification |
|---|---|---|---|---|
| Findings | DynamoDB / Table / Firestore | resource_id + evaluated_at | 13 months | INTERNAL |
| Waivers | DynamoDB | resource_id | until expiry + 12 months | INTERNAL |
| Audit log | S3 Object Lock | date/hour | 7 years (assumed policy) | CONFIDENTIAL |
| Standard | S3 versioned + Git | version | forever | PUBLIC-INTERNAL |
Lineage: cloud inventory -> adapters -> engine -> findings -> FOCUS tag join -> chargeback (diagram 19). No customer data or PII; `owner` is a team slug.
