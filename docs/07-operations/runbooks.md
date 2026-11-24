# Runbooks and SLOs
## SLOs
Detect-to-decision p95 < 5 min; remediation success >= 99%; inventory coverage >= 98%; hub availability 99.5%.
## Runbooks
- **Deploy:** `make test && make package`, apply module via pipeline (OIDC). **Rollback:** redeploy previous release tag; standard version is pinned per release.
- **DLQ not empty:** inspect message, fix adapter/parse bug, redrive; page if > 100 messages.
- **Region failover:** SSM runbook promotes region B, Route 53 flips, trigger full sweep, verify score recovers.
- **Mass false positive (bad standard release):** set `effect` to Audit in all clouds, pause remediation workflow, roll back registry release, run sweep, review plans in dry-run before re-enabling.
- **Key rotation:** CMK automatic annual rotation; verify alias and replica keys.
## Top failure scenarios
1 Event loss (sweep covers). 2 Bad standard release. 3 Writer permission drift. 4 API throttling (backoff, queue). 5 Region outage.
