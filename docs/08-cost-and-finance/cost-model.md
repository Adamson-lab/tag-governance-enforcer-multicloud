# Cost model (illustrative, assumptions stated)

> Maturity: design-validated. Unit prices below are placeholders to be refreshed with Infracost / cloud pricing calculators. AWS Config recorder and CloudTrail costs are excluded because they are assumed to exist already.

Assumptions: 15% of resources change per month; full sweep daily (30/month); Lambda 512 MB x 0.3s; 2% of evaluations need a remediation workflow (8 state transitions).

| Component | small (20k resources) | medium (150k) | large (1M) |
|---|---|---|---|
| EventBridge | $0.60 | $4.52 | $30.15 |
| SQS | $0.72 | $5.43 | $36.18 |
| Lambda | $1.63 | $12.21 | $81.41 |
| DynamoDB | $0.53 | $3.96 | $26.38 |
| Step Functions | $2.41 | $18.09 | $120.60 |
| S3 + Athena | $0.95 | $7.15 | $47.67 |
| Azure + GCP edges (assumed = 40% of AWS compute) | $0.89 | $6.69 | $44.62 |
| **Total / month** | **$7.74** | **$58.05** | **$387.01** |

## Unit economics

| Scale | Cost per 1,000 resources / month |
|---|---|
| small (20k resources) | $0.387 |
| medium (150k) | $0.387 |
| large (1M) | $0.387 |

## Sensitivity (medium scale)

| Change rate | Total / month |
|---|---|
| 5% | $57.88 |
| 15% | $58.05 |
| 30% | $58.30 |
| 50% | $58.64 |

## Value side (not a cost saving claim)

The enforcer makes spend attributable. Illustrative arithmetic: at $2.0M/month cloud spend, cutting untagged spend from 22% to 5% moves ~$340k/month from 'unallocated' to 'owned'. Waste reduction by owners is a separate, unproven benefit: at 0.5% / 1% / 2% of attributable spend it would be $8.5k / $17k / $34k per month. These are scenarios, not forecasts.

## Cost of delay and of downtime

An enforcer outage does not stop workloads (detective/corrective only; preventive controls are cloud-native). The cost of an outage is delayed correction, covered by the nightly sweep. This is why the DR target is a warm standby (RTO 60 min) rather than active/active (ADR-0007).
