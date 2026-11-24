# Test strategy
Unit (engine, adapters, remediation plans): done, 15 tests, see `evidence/unit-test-run.txt`. Policy: `opa test` (rego tests included, to run in CI). IaC: `terraform validate` in CI (not yet run). Integration, contract and load: pending Wave 1 sandbox. Resilience: failover drill and chaos (kill evaluator, flood queue) pending. Acceptance: score on sample inventory matches expected actions (`test_sample_inventory_and_scores`).
**Evidence honesty:** nothing in this repo claims production results. NFR targets are design targets until the Wave 1 evidence folder is populated.
