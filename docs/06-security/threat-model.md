# Threat model (STRIDE)
See diagrams 12 (trust boundaries) and 14 (threats).
| ID | Threat | STRIDE | Mitigation | Residual |
|---|---|---|---|---|
| T1 | Attacker sets plausible owner/cost-center to hide spend | Spoofing | Standard rules, owner must resolve to a known team list (Wave 2), change events audited | Medium |
| T2 | Writer role abused to change non-tag settings | Elevation | Tag-only permissions, permission boundary, IAM Access Analyzer checks | Low |
| T3 | Malicious tag values injected into tickets/dashboards | Tampering | Regex/enum validation, output encoding, no tag value is ever executed | Low |
| T4 | Event flood to exhaust the evaluator | DoS | SQS buffer, reserved concurrency, DLQ + alarm | Low |
| T5 | Findings or audit trail tampered | Repudiation | Object Lock, CloudTrail, separate log-archive account | Low |
| T6 | Tag metadata reveals org structure | Info disclosure | INTERNAL classification, RBAC on API, CMK encryption | Low |
## Control mapping (indicative)
NIST 800-53: CM-8 (inventory), CM-2, AC-6 (least privilege), AU-9/AU-11 (audit protection/retention). CIS Controls v8: 1, 3, 8. ISO 27001:2022: A.5.9, A.5.15, A.8.15. SOC 2: CC6.1, CC7.2. Formal mapping review by GRC pending.
