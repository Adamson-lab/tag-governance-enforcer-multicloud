from collections import Counter, defaultdict

GOOD = ("COMPLIANT", "EXEMPT")


def summarize(results):
    by_cloud = defaultdict(lambda: {"total": 0, "compliant": 0})
    for r in results:
        by_cloud[r.cloud]["total"] += 1
        by_cloud[r.cloud]["compliant"] += r.action in GOOD
    for v in by_cloud.values():
        v["score"] = round(100 * v["compliant"] / v["total"], 1) if v["total"] else 100.0
    total = len(results)
    ok = sum(v["compliant"] for v in by_cloud.values())
    return {"total": total, "score": round(100 * ok / total, 1) if total else 100.0,
            "by_action": dict(Counter(r.action for r in results)), "by_cloud": dict(by_cloud)}
