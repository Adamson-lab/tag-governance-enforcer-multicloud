.PHONY: test diagrams cost fmt package sample
PY=python3
test:
	PYTHONPATH=src $(PY) -m unittest discover -s tests -v
sample:
	PYTHONPATH=src $(PY) -m tagenforcer.cli examples/sample-inventory.json --today 2026-11-23 --out evidence/sample-run.json
diagrams:
	$(PY) diagrams/src/gen.py
cost:
	$(PY) scripts/cost_model.py docs/08-cost-and-finance/cost-model.md
fmt:
	terraform fmt -recursive infra
package:
	bash scripts/package_lambda.sh
