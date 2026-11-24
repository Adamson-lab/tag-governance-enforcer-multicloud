# Rollout (see diagram 20)
| Wave | Scope | Entry | Exit |
|---|---|---|---|
| 0 | Standard v1, sandbox deploy | ARB approval | tests green, sandbox evidence |
| 1 | Detect only, 3 clouds, read-only | Wave 0 exit | baseline score, owner coverage report, false-positive review |
| 2 | Auto-fix dev/sandbox, ticketing | Wave 1 exit | FP rate < 1%, rollback tested |
| 3 | Preventive: Audit -> Deny per cloud, CI gate required | Wave 2 exit | exception process live, comms done |
| 4 | Prod auto-fix in change windows, chargeback | Wave 3 exit | prod owner coverage >= 99% |
Cutover/rollback: every wave is a config switch (`effect`, remediation workflow enable) so rollback is minutes. Training: app-team 30-minute briefing, tag lookup page, PR template.
