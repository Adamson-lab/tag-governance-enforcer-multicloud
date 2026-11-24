import datetime as dt, json, unittest
from pathlib import Path
from tagenforcer import Resource, evaluate, load_standard, plan, summarize, to_cloud
from tagenforcer.adapters import from_aws_config, from_azure_graph, from_gcp_asset

STD = load_standard()
TODAY = dt.date(2026, 11, 23)
FULL = {"owner": "team-a", "cost-center": "cc-10001", "environment": "prod", "application": "app-one",
        "data-classification": "internal", "compliance-scope": "none", "managed-by": "terraform"}


def ev(cloud="aws", tags=None, parent=None, ex=None, rid="r1"):
    return evaluate(Resource(cloud, rid, "t", tags if tags is not None else dict(FULL), parent or {}), STD, TODAY, ex)


class EngineTests(unittest.TestCase):
    def test_compliant(self):
        self.assertEqual(ev().action, "COMPLIANT")

    def test_alias_and_case_autofix(self):
        t = {"Owner": "Team-A", "CostCenter": "CC-10001", "Env": "Prod", "App": "app-one",
             "DataClassification": "Internal", "compliance-scope": "none", "ManagedBy": "Terraform"}
        r = ev(tags=t)
        self.assertEqual(r.action, "AUTO_FIX")
        self.assertEqual(r.proposed_tags["cost-center"], "cc-10001")
        self.assertIn("CostCenter", r.remove_keys)

    def test_inheritance_for_inheritable_keys(self):
        t = {k: v for k, v in FULL.items() if k not in ("cost-center", "application")}
        r = ev(tags=t, parent={"CostCenter": "cc-10001", "app": "app-one"})
        self.assertEqual(r.action, "AUTO_FIX")
        self.assertEqual(r.changes, {"cost-center": "cc-10001", "application": "app-one"})

    def test_data_classification_is_never_inherited(self):
        t = {k: v for k, v in FULL.items() if k != "data-classification"}
        r = ev(tags=t, parent={"data-classification": "public"})
        self.assertEqual(r.action, "ESCALATE")

    def test_missing_owner_prod_escalates_nonprod_tickets(self):
        t = {k: v for k, v in FULL.items() if k != "owner"}
        self.assertEqual(ev(tags=t).action, "ESCALATE")
        t["environment"] = "dev"
        self.assertEqual(ev(tags=t).action, "TICKET")

    def test_invalid_enum_value_tickets(self):
        self.assertEqual(ev(tags=dict(FULL, environment="production")).action, "TICKET")

    def test_sandbox_requires_expiry(self):
        r = ev(tags=dict(FULL, environment="sandbox"))
        self.assertTrue(any(f.rule == "MISSING_REQUIRED" and f.key == "expiry" for f in r.findings))

    def test_expiry_lifecycle(self):
        base = dict(FULL, environment="sandbox")
        self.assertEqual(ev(tags=dict(base, expiry="2026-12-01")).action, "COMPLIANT")
        self.assertEqual(ev(tags=dict(base, expiry="2026-11-20")).action, "NOTIFY")
        self.assertEqual(ev(tags=dict(base, expiry="2026-11-01")).action, "EXPIRY_ENFORCE")
        self.assertEqual(ev(tags=dict(base, expiry="2026-13-45")).action, "TICKET")

    def test_system_tags_are_ignored(self):
        t = dict(FULL, **{"aws:cloudformation:stack-name": "x", "goog-managed-by": "y"})
        self.assertEqual(ev(tags=t).action, "COMPLIANT")

    def test_gcp_label_rules(self):
        self.assertEqual(ev("gcp").action, "COMPLIANT")
        r = ev("gcp", tags=dict(FULL, **{"Bad Key": "x"}))
        self.assertTrue(any(f.rule == "LIMIT" for f in r.findings))
        self.assertEqual(to_cloud("gcp", {"owner": "Team.A@x"}), {"owner": "team_a_x"})

    def test_conflicting_duplicate_keys_need_human(self):
        self.assertEqual(ev(tags=dict(FULL, CostCenter="cc-99999")).action, "TICKET")

    def test_exemption_valid_and_expired(self):
        self.assertEqual(ev(tags={}, ex={"r1": "2027-01-01"}).action, "EXEMPT")
        self.assertNotEqual(ev(tags={}, ex={"r1": "2026-01-01"}).action, "EXEMPT")

    def test_plan_per_cloud(self):
        for cloud, api in (("aws", "resourcegroupstaggingapi:TagResources"), ("azure", "Microsoft.Resources/tags"), ("gcp", "labels.update")):
            res = Resource(cloud, "id-1", "t", {"Owner": "Team-A", **{k: v for k, v in FULL.items() if k != "owner"}})
            out = evaluate(res, STD, TODAY)
            self.assertEqual(out.action, "AUTO_FIX")
            self.assertEqual(plan(out, res)[0]["api"], api)
        self.assertEqual(plan(ev(), Resource("aws", "r1")), [])

    def test_adapters(self):
        a = from_aws_config({"ARN": "arn:x", "resourceType": "AWS::S3::Bucket", "tags": {"Env": "dev"}, "awsAccountId": "1"})
        z = from_azure_graph({"id": "/s/1", "type": "t", "tags": None, "subscriptionId": "s"})
        g = from_gcp_asset({"name": "//x", "assetType": "t", "resource": {"data": {"labels": {"a": "b"}}}, "ancestors": ["projects/1"]})
        self.assertEqual((a.cloud, z.tags, g.tags, g.account), ("aws", {}, {"a": "b"}, "projects/1"))

    def test_sample_inventory_and_scores(self):
        d = json.loads((Path(__file__).parents[1] / "examples" / "sample-inventory.json").read_text())
        res = [evaluate(Resource(**r), STD, TODAY, d["exemptions"]) for r in d["resources"]]
        acts = {r.resource_id.split("/")[-1].split(":")[-1]: r.action for r in res}
        self.assertEqual(acts["i-0abc0001"], "AUTO_FIX")
        self.assertEqual(acts["orders-prod"], "ESCALATE")
        self.assertEqual(acts["vm-sbx9"], "EXPIRY_ENFORCE")
        self.assertEqual(acts["ledger"], "TICKET")
        self.assertEqual(acts["i-legacy0001"], "EXEMPT")
        s = summarize(res)
        self.assertEqual(s["total"], 11)
        self.assertEqual(set(s["by_cloud"]), {"aws", "azure", "gcp"})


if __name__ == "__main__":
    unittest.main()
