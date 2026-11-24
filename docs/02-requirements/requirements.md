# Requirements and traceability
## Functional
FR-1 Evaluate any resource against one standard. FR-2 Normalize aliases/case. FR-3 Inherit from parent scope (excluding data-classification). FR-4 Produce provider-specific fix plans. FR-5 Time-boxed waivers. FR-6 Sandbox expiry enforcement. FR-7 Compliance scorecard per cloud.
## Non-functional (quality attribute scenarios)
| ID | Scenario | Target |
|---|---|---|
| NFR-1 Latency | A tag change event arrives | decision within 5 min p95 |
| NFR-2 Availability | Hub region fails | RTO 60 min, RPO 5 min |
| NFR-3 Security | Writer role compromised | can only change tags; no data or IAM access |
| NFR-4 Correctness | Event dropped or duplicated | nightly sweep converges; handlers idempotent |
| NFR-5 Cost | Medium estate (150k resources) | under $100/month hub run cost (model) |
| NFR-6 Operability | Poison message | lands in DLQ, alarm pages on-call |
## Traceability matrix
| Requirement | Design element | Test / evidence |
|---|---|---|
| FR-1..FR-4 | `engine.py`, `remediation.py` | `tests/test_engine.py` (15 tests) |
| FR-5 | exemptions in `evaluate()` | `test_exemption_valid_and_expired` |
| FR-6 | expiry rules | `test_expiry_lifecycle` |
| NFR-3 | TagWriter role, diagram 13 | threat model T2; live IAM Access Analyzer run pending |
| NFR-1/2/4 | diagrams 09, 18 | load/failover tests pending (Wave 1) |
