#!/usr/bin/env python3
"""Diagram-as-code renderer with orthogonal wire routing (A* on a 10px grid).
Nodes are hard obstacles, wires spread across free tracks, steps are numbered badges described in a panel below.
Usage: python3 diagrams/src/gen.py [--preview DIR]   (writes diagrams/svg/*.svg, docs/diagram-index.md, diagrams/index.html)"""
import heapq, html, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from specs import SPECS, META

NW, NH, GX, GY, PAD, HEAD, ICON, C = 130, 110, 50, 40, 20, 40, 46, 10
TOP, BAND_GAP = 136, 90
KIND = {"compute": "#ED7100", "storage": "#7AA116", "db": "#3B48CC", "net": "#8C4FFF", "sec": "#DD344C",
        "mgmt": "#E7157B", "int": "#CC2264", "user": "#232F3E", "ext": "#5A6B86", "az": "#0078D4",
        "gcp": "#1A73E8", "data": "#8C4FFF"}
KNAME = {"compute": "Compute", "storage": "Storage", "db": "Database", "net": "Networking / API", "sec": "Security / identity",
         "mgmt": "Management & governance", "int": "Integration / events", "user": "People", "ext": "External system",
         "az": "Azure service", "gcp": "GCP service", "data": "Analytics"}
GCOL = {"aws": "#ED7100", "az": "#0078D4", "gcp": "#1A73E8", "ctl": "#232F3E", "sec": "#DD344C",
        "grn": "#3F8624", "gry": "#7D8998", "pur": "#8C4FFF"}
GICON = {"aws": "AWS", "az": "AZ", "gcp": "GCP", "ctl": "TG", "sec": "!", "grn": "OK", "gry": "", "pur": ""}
ESTYLE = {"": ("#232F3E", "", "m0"), "dash": ("#5A6B86", "7 5", "m1"), "red": ("#DD344C", "", "m2"), "ok": ("#3F8624", "", "m3")}
FONT = "'Amazon Ember','Segoe UI',Helvetica,Arial,sans-serif"
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]  # E S W N


def esc(s):
    return html.escape(str(s), quote=True)


def layout(spec):
    pos, boxes = {}, []
    band_x, band_w, prev, first, bottom = 40, 0, None, True, 0
    for g in spec["groups"]:
        cols = g.get("cols", 1)
        rows = -(-len(g["nodes"]) // cols)
        gw = 2 * PAD + cols * NW + (cols - 1) * GX
        gh = HEAD + rows * NH + (rows - 1) * GY + PAD
        if g.get("below") and prev:
            gx, gy = prev["x"], prev["y"] + prev["h"] + 40
            band_w = max(band_w, gw)
        else:
            if not first:
                band_x += band_w + BAND_GAP
            gx, gy, band_w = band_x, TOP, gw
        first = False
        prev = dict(x=gx, y=gy, w=gw, h=gh, g=g)
        boxes.append(prev)
        for i, nd in enumerate(g["nodes"]):
            r, c = divmod(i, cols)
            pos[nd[0]] = (gx + PAD + c * (NW + GX), gy + HEAD + r * (NH + GY), nd)
        bottom = max(bottom, gy + gh)
    return pos, boxes, band_x + band_w + 40, bottom


def node_cells(x, y):
    xi, m = x // C, (y - 6) // C
    return {(cx, cy) for cx in range(xi, xi + 13) for cy in range(m + 1, m + 12)}


def ports(x, y):
    """(side, slot) -> (port cell, outward dir idx, icon-edge anchor point). 3 slots per side so wires fan out."""
    xi, m = x // C, (y - 6) // C
    out = {}
    for sl in (-1, 0, 1):
        r = m + 3 + sl
        out[("R", sl)] = ((xi + 13, r), 0, (x + NW / 2 + ICON / 2, r * C + C / 2))
        out[("L", sl)] = ((xi - 1, r), 2, (x + NW / 2 - ICON / 2, r * C + C / 2))
        cc = xi + 6 + sl
        out[("T", sl)] = ((cc, m), 3, (cc * C + C / 2, y + 6))
        out[("B", sl)] = ((cc, m + 12), 1, (cc * C + C / 2, y + NH))
    return out


def center(c):
    return (c[0] * C + C / 2, c[1] * C + C / 2)


def astar(starts, goals, blocked, near, occ, W, H, ymin):
    gl = list(goals)
    h = lambda c: min(abs(c[0] - g[0]) + abs(c[1] - g[1]) for g in gl)
    pq, best, par, n = [], {}, {}, 0
    for c, d, pen in starts:
        s = (c, d); best[s] = pen; par[s] = None
        heapq.heappush(pq, (pen + h(c), n, pen, s)); n += 1
    while pq:
        _, _, g, s = heapq.heappop(pq)
        if g > best.get(s, 1e18):
            continue
        c, d = s
        if c in goals and goals[c] == d:
            out = []
            while s:
                out.append(s[0]); s = par[s]
            return out[::-1]
        for nd in (d, (d + 1) % 4, (d + 3) % 4):
            nc = (c[0] + DIRS[nd][0], c[1] + DIRS[nd][1])
            if not (0 <= nc[0] < W and ymin <= nc[1] < H) or nc in blocked:
                continue
            cost = 1 + (7 if nd != d else 0) + near.get(nc, 0)
            o = occ.get(nc)
            if o:
                cost += 10 if ("h" if nd % 2 == 0 else "v") in o else 3
            ng = g + cost; ns = (nc, nd)
            if ng < best.get(ns, 1e18):
                best[ns] = ng; par[ns] = s
                heapq.heappush(pq, (ng + h(nc), n, ng, ns)); n += 1
    return None


def simplify(pts):
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = out[-1], pts[i], pts[i + 1]
        if (a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1]):
            continue
        out.append(b)
    out.append(pts[-1])
    return out


def rounded(pts, r=7):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        la, lc = math.dist(a, b), math.dist(b, c)
        rr = min(r, la / 2, lc / 2)
        p1 = (b[0] - (b[0] - a[0]) / la * rr, b[1] - (b[1] - a[1]) / la * rr)
        p2 = (b[0] + (c[0] - b[0]) / lc * rr, b[1] + (c[1] - b[1]) / lc * rr)
        d += f" L{p1[0]:.1f},{p1[1]:.1f} Q{b[0]:.1f},{b[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"


def route_all(spec, pos, boxes, W, bottom):
    Wc, Hc, ymin = W // C + 1, (bottom + 50) // C + 1, 13
    blocked, near = set(), {}
    for x, y, _ in pos.values():
        blocked |= node_cells(x, y)
    for (cx, cy) in blocked:
        for dx, dy in DIRS:
            nb = (cx + dx, cy + dy)
            if nb not in blocked:
                near[nb] = 2
    for b in boxes:  # discourage running along group borders or through group title bars
        x0, x1, y0, y1 = b["x"] // C, (b["x"] + b["w"]) // C, b["y"] // C, (b["y"] + b["h"]) // C
        for cx in range(x0, x1 + 1):
            for cy in (y0, y1):
                near[(cx, cy)] = near.get((cx, cy), 0) + 5
            for cy in range(y0, (b["y"] + HEAD) // C + 1):
                near[(cx, cy)] = near.get((cx, cy), 0) + 3
        for cy in range(y0, y1 + 1):
            for cx in (x0, x1):
                near[(cx, cy)] = near.get((cx, cy), 0) + 5
    occ, routes, stats = {}, [], {"fallback": 0, "failed": 0}
    for e in spec["edges"]:
        a, b = e[0], e[1]
        assert a in pos and b in pos, f"{spec['slug']}: bad edge {a}->{b}"
        pa, pb = ports(*pos[a][:2]), ports(*pos[b][:2])
        starts = [(v[0], v[1], (0 if k[0] in "LR" else 3) + abs(k[1])) for k, v in pa.items()]
        goals = {v[0]: (v[1] + 2) % 4 for v in pb.values()}
        cells = astar(starts, goals, blocked, near, occ, Wc, Hc, ymin)
        if cells is None:
            stats["fallback"] += 1
            soft = {k: 60 for k in blocked}
            cells = astar(starts, goals, set(), {**near, **soft}, occ, Wc, Hc, ymin)
        if cells is None:
            stats["failed"] += 1
            routes.append(None); continue
        sside = next(k for k, v in pa.items() if v[0] == cells[0])
        dside = next(k for k, v in pb.items() if v[0] == cells[-1])
        pts = [pa[sside][2]] + [center(c) for c in cells] + [pb[dside][2]]
        pts = simplify(pts)
        for i in range(len(cells) - 1):
            o = "h" if cells[i][1] == cells[i + 1][1] else "v"
            for c in (cells[i], cells[i + 1]):
                occ.setdefault(c, set()).add(o)
        routes.append(pts)
    stats["shared"] = sum(1 for v in occ.values() if len(v) > 1)
    return routes, stats


def rect_dist(px, py, x, y, w, h):
    dx = max(x - px, 0, px - (x + w)); dy = max(y - py, 0, py - (y + h))
    return math.hypot(dx, dy)


def place_badges(routes, pos):
    placed, out, relaxed = [], [], 0
    rects = [(x, y, NW, NH) for x, y, _ in pos.values()]
    for pts in routes:
        if not pts:
            out.append(None); continue
        samples, acc = [], 0
        for i in range(len(pts) - 1):
            L = math.dist(pts[i], pts[i + 1])
            t = 0
            while t < L:
                samples.append((acc + t, pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t / L, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t / L))
                t += 5
            acc += L
        mid = acc / 2
        samples = [s for s in samples if 32 < s[0] < acc - 32] or samples
        samples.sort(key=lambda s: abs(s[0] - mid))
        choice = None
        for dmin, rmin in ((30, 18), (24, 14), (18, 10)):
            for _, sx, sy in samples:
                if all(math.dist((sx, sy), q) >= dmin for q in placed) and all(rect_dist(sx, sy, *r) >= rmin for r in rects):
                    choice = (sx, sy); break
            if choice:
                break
            relaxed += 1
        if not choice:  # last resort: the sample furthest from every other badge
            far = lambda sm: min([math.dist((sm[1], sm[2]), q) for q in placed] or [99]) + min(rect_dist(sm[1], sm[2], *r) for r in rects) * 0.5
            b = max(samples, key=far); choice = (b[1], b[2])
        placed.append(choice); out.append(choice)
    return out, relaxed


def render(num, spec, report):
    pos, boxes, right, bottom = layout(spec)
    W = max(right, 1180)
    routes, stats = route_all(spec, pos, boxes, W, bottom)
    badges, relaxed = place_badges(routes, pos)
    n_e = len(spec["edges"])
    cols = 3
    per = -(-n_e // cols)
    ly = bottom + 70
    py = ly + 60
    H = py + per * 19 + 70
    report.append((num, spec["slug"], n_e, stats["failed"], stats["fallback"], relaxed, stats["shared"]))
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="{FONT}">',
         '<defs><linearGradient id="sheen" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".28"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         '<filter id="sh" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="1.5" stdDeviation="1.6" flood-opacity=".25"/></filter>']
    for k, (c, _, m) in ESTYLE.items():
        o.append(f'<marker id="{m}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>')
    o.append('</defs>')
    o.append(f'<rect width="{W}" height="{H}" fill="#fff"/><rect width="{W}" height="64" fill="#232F3E"/><rect y="64" width="{W}" height="4" fill="#FF9900"/>')
    o.append(f'<text x="40" y="41" fill="#fff" font-size="23" font-weight="700">{esc(spec["title"])}</text>')
    o.append(f'<text x="{W-40}" y="40" fill="#FF9900" font-size="13" font-weight="700" text-anchor="end">DIAGRAM {num:02d} / {len(SPECS)}</text>')
    o.append(f'<text x="40" y="96" fill="#232F3E" font-size="14.5">{esc(spec["sub"])}</text>')
    o.append(f'<text x="40" y="118" fill="#5A6B86" font-size="11.5">Audience: {esc(spec["audience"])}  |  Notation: {esc(spec["notation"])}  |  Scope: {esc(spec["scope"])}</text>')
    for b in boxes:
        g = b["g"]; c = GCOL[g.get("color", "gry")]; tb = g.get("style") == "tb"
        o.append(f'<rect x="{b["x"]}" y="{b["y"]}" width="{b["w"]}" height="{b["h"]}" rx="6" fill="{c}" fill-opacity=".04" stroke="{c}" stroke-width="{2.6 if tb else 1.5}" stroke-dasharray="{"10 4 2 4" if tb else "7 4"}"/>')
        ic = GICON.get(g.get("color", "gry"), "")
        o.append(f'<rect x="{b["x"]}" y="{b["y"]}" width="30" height="30" fill="{c}"/>')
        if ic:
            o.append(f'<text x="{b["x"]+15}" y="{b["y"]+19}" fill="#fff" font-size="9.5" font-weight="700" text-anchor="middle">{esc(ic)}</text>')
        o.append(f'<text x="{b["x"]+38}" y="{b["y"]+20}" fill="{c}" font-size="12.5" font-weight="700">{esc(g["label"])}</text>')
    for e, pts in zip(spec["edges"], routes):
        if not pts:
            continue
        col, dash, mk = ESTYLE[e[3] if len(e) > 3 else ""]
        da = f' stroke-dasharray="{dash}"' if dash else ""
        o.append(f'<path d="{rounded(pts)}" fill="none" stroke="{col}" stroke-width="1.8"{da} marker-end="url(#{mk})"/>')
    used = []
    for nid, (x, y, nd) in pos.items():
        kind, abbr = nd[2], nd[3]
        used.append(kind)
        c = KIND[kind]
        ix = x + NW / 2 - ICON / 2
        o.append(f'<g filter="url(#sh)"><rect x="{ix}" y="{y+6}" width="{ICON}" height="{ICON}" rx="7" fill="{c}"/><rect x="{ix}" y="{y+6}" width="{ICON}" height="{ICON}" rx="7" fill="url(#sheen)"/></g>')
        o.append(f'<text x="{x+NW/2}" y="{y+6+ICON/2+5}" fill="#fff" font-size="{13 if len(abbr)<4 else 11}" font-weight="700" text-anchor="middle">{esc(abbr)}</text>')
        for i, ln in enumerate(nd[1].split("|")[:2]):
            o.append(f'<text x="{x+NW/2}" y="{y+ICON+22+i*13}" fill="{"#232F3E" if i==0 else "#5A6B86"}" font-size="{11.5 if i==0 else 10}" font-weight="{600 if i==0 else 400}" text-anchor="middle">{esc(ln)}</text>')
        if len(nd) > 4 and nd[4]:
            o.append(f'<text x="{x+NW/2}" y="{y+ICON+48}" fill="#8A94A6" font-size="9" text-anchor="middle">{esc(nd[4])}</text>')
    for i, (e, bp) in enumerate(zip(spec["edges"], badges), 1):
        if not bp:
            continue
        col = ESTYLE[e[3] if len(e) > 3 else ""][0]
        o.append(f'<circle cx="{bp[0]:.1f}" cy="{bp[1]:.1f}" r="9" fill="{col}" stroke="#fff" stroke-width="1.5"/><text x="{bp[0]:.1f}" y="{bp[1]+3.6:.1f}" fill="#fff" font-size="10" font-weight="700" text-anchor="middle">{i}</text>')
    # legend
    o.append(f'<line x1="40" y1="{ly-16}" x2="{W-40}" y2="{ly-16}" stroke="#D5DBDB"/><text x="40" y="{ly+4}" fill="#232F3E" font-size="11" font-weight="700">LEGEND</text>')
    lx, legend = 110, spec.get("legend", {})
    for k in dict.fromkeys(used):
        name = legend.get(k, KNAME[k])
        o.append(f'<rect x="{lx}" y="{ly-8}" width="16" height="16" rx="3" fill="{KIND[k]}"/><text x="{lx+22}" y="{ly+4}" font-size="10.5" fill="#232F3E">{esc(name)}</text>')
        lx += 40 + len(name) * 5.6
    ly2, lx = ly + 26, 110
    for st, name in (("", "synchronous"), ("dash", "async / event"), ("red", "deny / failure"), ("ok", "success / write-back")):
        c, dsh, _ = ESTYLE[st]
        o.append(f'<line x1="{lx}" y1="{ly2}" x2="{lx+34}" y2="{ly2}" stroke="{c}" stroke-width="2"' + (f' stroke-dasharray="{dsh}"' if dsh else "") + f'/><text x="{lx+42}" y="{ly2+4}" font-size="10.5" fill="#232F3E">{name}</text>')
        lx += 70 + len(name) * 5.6
    o.append(f'<rect x="{lx}" y="{ly2-8}" width="46" height="16" fill="none" stroke="#DD344C" stroke-width="2" stroke-dasharray="10 4 2 4"/><text x="{lx+54}" y="{ly2+4}" font-size="10.5" fill="#232F3E">trust boundary</text>')
    # numbered step panel
    o.append(f'<text x="40" y="{py-8}" font-size="11" font-weight="700" fill="#232F3E">FLOW STEPS</text>')
    colw = (W - 80) / cols
    short = lambda i: pos[i][2][1].split("|")[0]
    for i, e in enumerate(spec["edges"]):
        cx, cy = 40 + (i // per) * colw, py + (i % per) * 19
        col = ESTYLE[e[3] if len(e) > 3 else ""][0]
        txt = f"{e[2]}  ({short(e[0])} > {short(e[1])})"
        mx = int(colw / 5.5) - 5
        txt = txt if len(txt) <= mx else txt[:mx - 1] + "..."
        o.append(f'<circle cx="{cx+8}" cy="{cy}" r="8" fill="{col}"/><text x="{cx+8}" y="{cy+3.5}" fill="#fff" font-size="9.5" font-weight="700" text-anchor="middle">{i+1}</text><text x="{cx+22}" y="{cy+4}" font-size="10.5" fill="#232F3E">{esc(txt)}</text>')
    for i, t in enumerate(spec.get("notes", [])[:2]):
        o.append(f'<text x="40" y="{H-34+i*14}" font-size="10.5" fill="#232F3E"><tspan font-weight="700">Note:</tspan> {esc(t)}</text>')
    o.append(f'<text x="40" y="{H-8}" font-size="9.5" fill="#8A94A6">{esc(META)} | Diagram {num:02d} v1.1.0 | 2026-11-23 | Author: Favour Adamson | Synthetic placeholders only: no real account IDs.</text></svg>')
    return "\n".join(o), (pos, boxes, routes, badges, W, H)


def preview(path, data, spec):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    pos, boxes, routes, badges, W, H = data
    im = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(im)
    for b in boxes:
        d.rectangle([b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]], outline=GCOL[b["g"].get("color", "gry")], width=2)
        d.text((b["x"] + 36, b["y"] + 10), b["g"]["label"][:40], fill="black")
    for e, pts in zip(spec["edges"], routes):
        if pts:
            d.line(pts, fill=ESTYLE[e[3] if len(e) > 3 else ""][0], width=2)
    for x, y, nd in pos.values():
        d.rectangle([x + 42, y + 6, x + 88, y + 52], fill=KIND[nd[2]]); d.text((x + 50, y + 22), nd[3], fill="white")
        d.text((x + 8, y + 58), nd[1].split("|")[0][:22], fill="black")
    for i, bp in enumerate(badges, 1):
        if bp:
            d.ellipse([bp[0] - 9, bp[1] - 9, bp[0] + 9, bp[1] + 9], fill="#232F3E"); d.text((bp[0] - 5, bp[1] - 5), str(i), fill="white")
    im.save(path)


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out = os.path.join(root, "diagrams", "svg")
    os.makedirs(out, exist_ok=True)
    pv = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    if pv:
        os.makedirs(pv, exist_ok=True)
    rows, gal, report = [], [], []
    for i, s in enumerate(SPECS, 1):
        name = f"{i:02d}-{s['slug']}.svg"
        svg, data = render(i, s, report)
        open(os.path.join(out, name), "w", encoding="utf-8").write(svg)
        if pv:
            preview(os.path.join(pv, f"{i:02d}.png"), data, s)
        rows.append(f"| {i:02d} | [{s['title']}](../diagrams/svg/{name}) | {s['audience']} | {s['notation']} | 2026-11-23 |")
        gal.append(f'<figure><a href="svg/{name}"><img src="svg/{name}" alt="{esc(s["title"])}"></a><figcaption>{i:02d}. {esc(s["title"])}</figcaption></figure>')
    open(os.path.join(root, "docs", "diagram-index.md"), "w", encoding="utf-8").write(
        "# Diagram index\n\nAll diagrams are generated from `diagrams/src/specs.py` by `diagrams/src/gen.py` (orthogonal auto-routing, numbered steps), so they cannot drift from source.\n\n"
        "| # | Diagram | Audience | Notation | Last review |\n|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    open(os.path.join(root, "diagrams", "index.html"), "w", encoding="utf-8").write(
        "<!doctype html><meta charset=utf-8><title>Tag Governance Enforcer - diagram gallery</title><style>body{font-family:Segoe UI,Arial;margin:24px;background:#f2f3f3}"
        "figure{background:#fff;margin:0 0 28px;padding:12px;border:1px solid #d5dbdb}img{width:100%}figcaption{font-weight:600;padding-top:8px}</style><h1>Tag Governance Enforcer: 20 architecture diagrams</h1>" + "".join(gal))
    print("diag slug edges unrouted fallback badge-relaxed shared-cells")
    for r in report:
        print(*r)
    print(f"rendered {len(SPECS)} diagrams")


if __name__ == "__main__":
    main()
