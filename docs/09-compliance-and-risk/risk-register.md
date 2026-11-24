# Risk register
| ID | Risk | L | I | Owner | Mitigation | Residual |
|---|---|---|---|---|---|---|
| R-01 | Bad standard release causes mass wrong fixes | M | H | CCoE | dry-run, staged waves, rollback | M |
| R-02 | Auto-fix hits resources owned by other automation (tag fights) | H | M | Platform | managed-by awareness, backoff, conflict ticket | M |
| R-03 | Tag-on-create unsupported for some services | H | L | CCoE | detective+corrective layers | L |
| R-04 | Compromised cloud admin edits tags directly | L | H | Security | detective loop, audit trail | M |
| R-05 | Hub cloud concentration (AWS) | L | M | Architecture | neutral engine, exit plan below | L |
| R-06 | Owners ignore tickets | H | M | FinOps | SLA, escalation, showback visibility | M |
## FMEA (critical path)
Event delivery fails -> sweep catches (detect delay <= 24 h). Evaluator throws -> DLQ + alarm. Writer denied -> verify step fails -> ticket. State store unavailable -> queue retains up to 14 days.
## Exit and portability
The engine is pure Python with no SDK imports; the hub can move to Azure or GCP by re-implementing the thin handlers and workflow definitions. Standard and policies are provider-neutral JSON/Rego.
