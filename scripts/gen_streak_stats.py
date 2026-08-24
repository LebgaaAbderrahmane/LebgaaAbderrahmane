import datetime
import json
import os
import sys

ACCENT = "#36BCF7"
BG = "#0d1117"
MUTED = "#c9d1d9"
DIVIDER = "#21262d"

source = sys.argv[1] if len(sys.argv) > 1 else "calendar.json"
with open(source) as f:
    payload = json.load(f)

if "errors" in payload or payload.get("data", {}).get("user") is None:
    raise SystemExit(f"GitHub API error: {json.dumps(payload)[:300]}")

days = []
for week in payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]:
    for day in week["contributionDays"]:
        days.append((datetime.date.fromisoformat(day["date"]), day["contributionCount"]))
days.sort(key=lambda d: d[0])

total = sum(count for _, count in days)

longest = 0
current_run = 0
for _, count in days:
    current_run = current_run + 1 if count > 0 else 0
    longest = max(longest, current_run)

current = 0
i = len(days) - 1
if i >= 0 and days[i][1] == 0:
    i -= 1
while i >= 0 and days[i][1] > 0:
    current += 1
    i -= 1


def stat_block(cx, value, unit, label):
    parts = [
        f'<text x="{cx}" y="72" text-anchor="middle" font-family=\'Segoe UI, Ubuntu, sans-serif\' font-size="13" fill="{MUTED}">{label}</text>',
        f'<text x="{cx}" y="118" text-anchor="middle" font-family=\'Segoe UI, Ubuntu, sans-serif\' font-size="36" font-weight="600" fill="{ACCENT}">{value}</text>',
    ]
    if unit:
        parts.append(
            f'<text x="{cx}" y="142" text-anchor="middle" font-family=\'Segoe UI, Ubuntu, sans-serif\' font-size="14" fill="{ACCENT}">{unit}</text>'
        )
    return "\n".join(parts)


svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="Streak stats">
  <rect width="495" height="195" fill="{BG}" rx="4.5"/>
  <line x1="165" y1="38" x2="165" y2="157" stroke="{DIVIDER}" stroke-width="1"/>
  <line x1="330" y1="38" x2="330" y2="157" stroke="{DIVIDER}" stroke-width="1"/>
  {stat_block(82, f"{total:,}", "", "Total Contributions")}
  {stat_block(247, str(current), "days" if current != 1 else "day", "Current Streak")}
  {stat_block(412, str(longest), "days" if longest != 1 else "day", "Longest Streak")}
</svg>
"""

os.makedirs("streak-stats", exist_ok=True)
with open("streak-stats/streak.svg", "w") as f:
    f.write(svg)

print(f"total={total:,} current={current} longest={longest}")
