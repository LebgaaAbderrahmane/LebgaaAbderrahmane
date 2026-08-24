import datetime
import json
import math
import os
import sys

ACCENT = "#36BCF7"
BG = "#0d1117"
MUTED = "#c9d1d9"
DIVIDER = "#21262d"
BAR_DIM = "#1f6feb"

W = 830
H = 200

source = sys.argv[1] if len(sys.argv) > 1 else "cards.json"
with open(source) as f:
    payload = json.load(f)

if "errors" in payload or payload.get("data", {}).get("user") is None:
    raise SystemExit(f"GitHub API error: {json.dumps(payload)[:300]}")

user = payload["data"]["user"]
coll = user["contributionsCollection"]
repos = [r for r in user["repositories"]["nodes"] if r is not None]

FONT = "Segoe UI, Ubuntu, sans-serif"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wrap(inner):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img">\n'
        f'  <rect width="{W}" height="{H}" fill="{BG}" rx="4.5"/>\n{inner}\n</svg>\n'
    )


def save(name, inner):
    os.makedirs("cards", exist_ok=True)
    with open(f"cards/{name}.svg", "w") as f:
        f.write(wrap(inner))
    print(f"cards/{name}.svg written")


def label(cx, y, text, size, fill, weight="400", anchor="middle"):
    return (
        f'<text x="{cx}" y="{y}" text-anchor="{anchor}" font-family=\'{FONT}\' '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'
    )


# ---------------- stats ----------------
total_stars = sum(r.get("stargazerCount") or 0 for r in repos)
commits = coll.get("totalCommitContributions") or 0
prs = coll.get("totalPullRequestContributions") or 0
issues = coll.get("totalIssueContributions") or 0
contributed_to = (user.get("repositoriesContributedTo") or {}).get("totalCount", 0)

stats = [
    ("Stars", f"{total_stars:,}"),
    ("Commits (this year)", f"{commits:,}"),
    ("Pull Requests", f"{prs:,}"),
    ("Issues", f"{issues:,}"),
    ("Contributed to", f"{contributed_to:,}"),
]
parts = []
step = W / len(stats)
for i, (lab, val) in enumerate(stats):
    cx = step * i + step / 2
    parts.append(label(cx, 82, lab, 13, MUTED))
    parts.append(label(cx, 128, val, 34, ACCENT, weight="600"))
    if i > 0:
        parts.append(
            f'<line x1="{step * i:.0f}" y1="48" x2="{step * i:.0f}" y2="152" stroke="{DIVIDER}"/>'
        )
save("stats", "\n".join(parts))

# ---------------- languages donut ----------------
lang_bytes = {}
lang_colors = {}
for r in repos:
    for edge in ((r.get("languages") or {}).get("edges") or []):
        node = edge["node"]
        if node and edge.get("size"):
            lang_bytes[node["name"]] = lang_bytes.get(node["name"], 0) + edge["size"]
            if node.get("color"):
                lang_colors.setdefault(node["name"], node["color"])

top = sorted(lang_bytes.items(), key=lambda kv: kv[1], reverse=True)[:6]
grand = sum(v for _, v in top) or 1
fallback = ["#3178c6", "#b07219", "#3572A5", "#a371f7", "#f1e05a", "#89e051"]

inner = ['<g transform="translate(150,100)">']
cx, cy, r, sw = 0, 0, 62, 30
angle = -math.pi / 2
legend = []
for i, (name, size) in enumerate(top):
    frac = size / grand
    a1 = angle + frac * 2 * math.pi
    x0, y0 = cx + r * math.cos(angle), cy + r * math.sin(angle)
    x1, y1 = cx + r * math.cos(a1), cy + r * math.sin(a1)
    large = 1 if (a1 - angle) > math.pi else 0
    color = lang_colors.get(name) or fallback[i % len(fallback)]
    inner.append(
        f'<path d="M {x0:.2f} {y0:.2f} A {r} {r} 0 {large} 1 {x1:.2f} {y1:.2f}" '
        f'fill="none" stroke="{color or fallback[i % len(fallback)]}" stroke-width="{sw}" '
        f'stroke-linecap="butt"/>'
    )
    legend.append((name, frac, lang_colors.get(name) or fallback[i % len(fallback)]))
    angle = a1
inner.append("</g>")
lx = 330
for i, (name, frac, color) in enumerate(legend):
    y = 42 + i * 26
    inner.append(f'<rect x="{lx}" y="{y - 11}" width="14" height="14" rx="3" fill="{color}"/>')
    inner.append(
        f'<text x="{lx + 22}" y="{y + 1}" font-family=\'{FONT}\' font-size="15" fill="{MUTED}">'
        f'{esc(name)} <tspan fill="{ACCENT}">{frac * 100:.1f}%</tspan></text>'
    )
inner.append(label(W / 2 + 130, 178, f"{len(lang_bytes)} languages across {len(repos)} repos", 12, MUTED))
save("languages", "\n".join(inner))

# ---------------- monthly activity ----------------
days = []
for week in coll["contributionCalendar"]["weeks"]:
    for d in week["contributionDays"]:
        days.append((datetime.date.fromisoformat(d["date"]), d["contributionCount"]))
days.sort(key=lambda d: d[0])

months = {}
for d, c in days:
    key = (d.year, d.month)
    months[key] = months.get(key, 0) + c
keys = sorted(months)[-12:]
vals = [months[k] for k in keys]

plot_x0, plot_x1, base_y, top_y = 70, W - 50, 155, 45
bw = (plot_x1 - plot_x0) / len(vals)
vmax = max(vals) or 1
parts = []
for i, v in enumerate(vals):
    h = (v / vmax) * (base_y - top_y)
    x = plot_x0 + i * bw + bw * 0.18
    parts.append(
        f'<rect x="{x:.1f}" y="{base_y - h:.1f}" width="{bw * 0.64:.1f}" height="{h:.1f}" rx="3" fill="{ACCENT}"/>'
    )
    m = datetime.date(keys[i][0], keys[i][1], 1).strftime("%b")
    parts.append(label(plot_x0 + i * bw + bw / 2, 176, m, 11, MUTED))
    parts.append(label(plot_x0 + i * bw + bw / 2, base_y - h - 6, f"{v:,}", 10, MUTED))
parts.append(f'<line x1="{plot_x0}" y1="{base_y}" x2="{plot_x1}" y2="{base_y}" stroke="{DIVIDER}"/>')
parts.append(label(W / 2, 28, "Contributions per month", 13, MUTED))
save("activity", "\n".join(parts))

# ---------------- streak ----------------
longest = 0
run = 0
for _, c in days:
    run = run + 1 if c > 0 else 0
    longest = max(longest, run)
current = 0
i = len(days) - 1
if i >= 0 and days[i][1] == 0:
    i -= 1
while i >= 0 and days[i][1] > 0:
    current += 1
    i -= 1
total = sum(c for _, c in days)

cols = [
    (W / 6, f"{total:,}", "", "Total Contributions"),
    (W / 2, str(current), "days" if current != 1 else "day", "Current Streak"),
    (W * 5 / 6, str(longest), "days" if longest != 1 else "day", "Longest Streak"),
]
parts = []
for i, (cx, val, unit, lab) in enumerate(cols):
    parts.append(label(cx, 82, lab, 13, MUTED))
    parts.append(label(cx, 128, val, 34, ACCENT, weight="600"))
    if unit:
        parts.append(label(cx, 148, unit, 14, ACCENT))
    if i > 0:
        x = W / 3 * i
        parts.append(f'<line x1="{x:.0f}" y1="52" x2="{x:.0f}" y2="150" stroke="{DIVIDER}"/>')
save("streak", "\n".join(parts))

print(
    f"stats: stars={total_stars} commits={commits} prs={prs} issues={issues} contributed={contributed_to}"
)
print(f"streak: current={current} longest={longest} | langs={len(lang_bytes)} | months={len(vals)}")
