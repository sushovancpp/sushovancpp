import json
import os
import urllib.request
from datetime import datetime, timedelta

USERNAME = "sushovancpp"
TOKEN = os.environ["GH_PRIVATE_TOKEN"]

GRAPHQL_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

today = datetime.utcnow()
start = today - timedelta(days=365)

variables = {
    "login": USERNAME,
    "from": start.strftime("%Y-%m-%dT00:00:00Z"),
    "to": today.strftime("%Y-%m-%dT23:59:59Z"),
}

payload = json.dumps({
    "query": GRAPHQL_QUERY,
    "variables": variables,
}).encode("utf-8")

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": USERNAME,
    },
)

with urllib.request.urlopen(request) as response:
    data = json.loads(response.read().decode("utf-8"))

if "errors" in data:
    raise RuntimeError(json.dumps(data["errors"], indent=2))

calendar = (
    data["data"]["user"]["contributionsCollection"]
    ["contributionCalendar"]
)

weeks = calendar["weeks"]
total = calendar["totalContributions"]

# SVG dimensions
CELL = 12
GAP = 4
LEFT = 40
TOP = 45
WIDTH = LEFT + len(weeks) * (CELL + GAP) + 20
HEIGHT = TOP + 7 * (CELL + GAP) + 35

FONT = (
    "ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"
    "Segoe UI,Roboto,Helvetica,Arial,sans-serif"
)

svg = []

svg.append(
    f'<svg xmlns="http://www.w3.org/2000/svg" '
    f'width="{WIDTH}" height="{HEIGHT}" '
    f'viewBox="0 0 {WIDTH} {HEIGHT}">'
)

svg.append(
    '<rect width="100%" height="100%" rx="10" fill="transparent"/>'
)

svg.append(
    f'<text x="{LEFT}" y="22" '
    f'font-family="{FONT}" font-size="14" '
    f'font-weight="600" fill="#58A6FF">'
    f'{total:,} contributions in the last year'
    f'</text>'
)

# Day labels
day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]

for day, label in enumerate(day_labels):
    if label:
        y = TOP + day * (CELL + GAP) + 10
        svg.append(
            f'<text x="2" y="{y}" '
            f'font-family="{FONT}" font-size="9" '
            f'fill="#8B949E">{label}</text>'
        )

# Contribution cells
for week_index, week in enumerate(weeks):
    for day_index, contribution in enumerate(
        week["contributionDays"]
    ):
        x = LEFT + week_index * (CELL + GAP)
        y = TOP + day_index * (CELL + GAP)

        count = contribution["contributionCount"]
        color = contribution["color"]

        svg.append(
            f'<rect x="{x}" y="{y}" '
            f'width="{CELL}" height="{CELL}" rx="3" '
            f'fill="{color}">'
            f'<title>{contribution["date"]}: '
            f'{count} contribution'
            f'{"s" if count != 1 else ""}</title>'
            f'</rect>'
        )

# Legend
legend_y = HEIGHT - 18

svg.append(
    f'<text x="{LEFT}" y="{legend_y}" '
    f'font-family="{FONT}" font-size="9" '
    f'fill="#8B949E">Less</text>'
)

legend_colors = [
    "#161B22",
    "#0E4429",
    "#006D32",
    "#26A641",
    "#39D353",
]

for i, color in enumerate(legend_colors):
    x = LEFT + 28 + i * 17

    svg.append(
        f'<rect x="{x}" y="{legend_y - 9}" '
        f'width="11" height="11" rx="2" fill="{color}"/>'
    )

svg.append(
    f'<text x="{LEFT + 120}" y="{legend_y}" '
    f'font-family="{FONT}" font-size="9" '
    f'fill="#8B949E">More</text>'
)

svg.append("</svg>")

os.makedirs("assets", exist_ok=True)

with open(
    "assets/contributions.svg",
    "w",
    encoding="utf-8"
) as file:
    file.write("\n".join(svg))

print(f"Generated graph with {total:,} contributions.")
