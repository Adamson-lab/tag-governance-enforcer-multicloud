# Contributing
- Trunk-based: short-lived branches, every change via PR (fill the template: what, why, risk, test evidence, rollback).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Changing the tag standard? Open an ADR first (`docs/04-adr/`), bump `policies/tag-standard.json` version, add tests.
- Diagrams are code: edit `diagrams/src/specs.py`, run `make diagrams`, commit both.
- Never commit real account IDs, secrets, or employer-confidential material.
