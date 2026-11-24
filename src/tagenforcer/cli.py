import argparse, datetime as dt, json
from dataclasses import asdict
from .engine import Resource, evaluate, load_standard
from .remediation import plan
from .report import summarize


def main(argv=None):
    ap = argparse.ArgumentParser(description="Evaluate an inventory file against the tag standard")
    ap.add_argument("inventory")
    ap.add_argument("--today")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    data = json.load(open(a.inventory, encoding="utf-8"))
    std = load_standard()
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    rows = []
    for r in data["resources"]:
        res = Resource(**r)
        out = evaluate(res, std, today, data.get("exemptions"))
        rows.append((res, out))
    s = summarize([o for _, o in rows])
    print(f"{'CLOUD':6} {'ACTION':15} RESOURCE")
    for res, o in rows:
        print(f"{o.cloud:6} {o.action:15} {res.id}")
    print(f"\nscore={s['score']}%  total={s['total']}  actions={s['by_action']}")
    if a.out:
        payload = {"standard_version": std["version"], "evaluated_on": str(today), "summary": s,
                   "results": [asdict(o) | {"plan": plan(o, res)} for res, o in rows]}
        json.dump(payload, open(a.out, "w", encoding="utf-8"), indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
