#!/usr/bin/env python3
"""Illustrative run-cost model for the AWS hub. ALL unit prices are assumptions: refresh with Infracost / pricing calculator before quoting."""
import sys
P = {"lambda_req_per_m": 0.20, "lambda_gb_s": 0.0000166667, "ddb_wru_per_m": 1.25, "ddb_rru_per_m": 0.25, "sfn_trans_per_m": 25.0,
     "eventbridge_per_m": 1.0, "sqs_per_m": 0.40, "s3_gb": 0.023, "athena_per_tb": 5.0}
SCALES = {"small (20k resources)": 20_000, "medium (150k)": 150_000, "large (1M)": 1_000_000}
CHANGE_RATE, SWEEPS, MEM_GB, SECS = 0.15, 30, 0.5, 0.3  # monthly change events per resource, sweeps per month


def run(n):
    ev = n * CHANGE_RATE + n * SWEEPS           # events + sweep evaluations per month
    fix = ev * 0.02                              # share needing remediation workflow (assumption)
    c = {"EventBridge": ev * P["eventbridge_per_m"] / 1e6, "SQS": ev * 3 * P["sqs_per_m"] / 1e6,
         "Lambda": ev * P["lambda_req_per_m"] / 1e6 + ev * MEM_GB * SECS * P["lambda_gb_s"],
         "DynamoDB": ev * 0.5 * P["ddb_wru_per_m"] / 1e6 + ev * P["ddb_rru_per_m"] / 1e6,
         "Step Functions": fix * 8 * P["sfn_trans_per_m"] / 1e6,
         "S3 + Athena": n * 2e-6 * 1000 * P["s3_gb"] + 0.05 * P["athena_per_tb"] * (n / 150_000)}
    c["Azure + GCP edges (assumed = 40% of AWS compute)"] = 0.4 * (c["Lambda"] + c["EventBridge"])
    return c


if __name__ == "__main__":
    lines = ["# Cost model (illustrative, assumptions stated)", "",
             "> Maturity: design-validated. Unit prices below are placeholders to be refreshed with Infracost / cloud pricing calculators. AWS Config recorder and CloudTrail costs are excluded because they are assumed to exist already.", "",
             f"Assumptions: {CHANGE_RATE:.0%} of resources change per month; full sweep daily ({SWEEPS}/month); Lambda {int(MEM_GB*1024)} MB x {SECS}s; 2% of evaluations need a remediation workflow (8 state transitions).", "",
             "| Component | " + " | ".join(SCALES) + " |", "|---|" + "---|" * len(SCALES)]
    res = {k: run(v) for k, v in SCALES.items()}
    for comp in next(iter(res.values())):
        lines.append(f"| {comp} | " + " | ".join(f"${res[k][comp]:,.2f}" for k in SCALES) + " |")
    lines.append("| **Total / month** | " + " | ".join(f"**${sum(res[k].values()):,.2f}**" for k in SCALES) + " |")
    lines += ["", "## Unit economics", "", "| Scale | Cost per 1,000 resources / month |", "|---|---|"]
    lines += [f"| {k} | ${sum(res[k].values())/(v/1000):,.3f} |" for k, v in SCALES.items()]
    lines += ["", "## Sensitivity (medium scale)", "", "| Change rate | Total / month |", "|---|---|"]
    for cr in (0.05, 0.15, 0.30, 0.50):
        CHANGE_RATE = cr
        lines.append(f"| {cr:.0%} | ${sum(run(150_000).values()):,.2f} |")
    CHANGE_RATE = 0.15
    lines += ["", "## Value side (not a cost saving claim)", "",
              "The enforcer makes spend attributable. Illustrative arithmetic: at $2.0M/month cloud spend, cutting untagged spend from 22% to 5% moves ~$340k/month from 'unallocated' to 'owned'. "
              "Waste reduction by owners is a separate, unproven benefit: at 0.5% / 1% / 2% of attributable spend it would be $8.5k / $17k / $34k per month. These are scenarios, not forecasts.", "",
              "## Cost of delay and of downtime", "",
              "An enforcer outage does not stop workloads (detective/corrective only; preventive controls are cloud-native). The cost of an outage is delayed correction, covered by the nightly sweep. This is why the DR target is a warm standby (RTO 60 min) rather than active/active (ADR-0007)."]
    out = "\n".join(lines) + "\n"
    open(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout", "w").write(out)
