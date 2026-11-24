# Business case, stakeholders, KPIs
## Stakeholders and RACI
| Activity | CCoE | FinOps | Security/GRC | App teams | Audit |
|---|---|---|---|---|---|
| Own tag standard | A/R | C | C | I | I |
| Approve standard changes (ARB) | R | C | C | C | I |
| Fix own resources' tags | I | I | I | A/R | I |
| Approve exceptions/waivers | R | C | A | C | I |
| Review compliance evidence | I | I | R | I | A |
## Drivers and constraints
Drivers: chargeback accuracy, incident routing, audit evidence, M&A onboarding. Constraints: GCP label charset, native tag-on-create gaps, no customer data in scope, least-privilege writers.
## KPIs (baseline assumed until measured in Wave 1)
| KPI | Baseline | Target |
|---|---|---|
| Untagged spend share | 22% (assumed) | < 5% |
| Resources with valid owner (prod) | unknown | >= 99% |
| Median time to detect a bad tag | days (manual) | < 5 min (event path) |
| Auto-fixed share of findings | 0% | >= 60% |
| False-positive remediations | n/a | < 1% |
See `docs/08-cost-and-finance/cost-model.md` for run cost and the value arithmetic (scenarios, not forecasts).
