import requests
import os
from pathlib import Path

# ロゴ保存先
logo_dir = Path("templates/logos")
logo_dir.mkdir(exist_ok=True)

# チームIDとロゴURL
teams = {
    "NYY": "147", "BOS": "111", "TB": "139", "BAL": "110", "TOR": "141",
    "CWS": "145", "CLE": "114", "DET": "116", "KC": "118", "MIN": "142",
    "HOU": "117", "TEX": "140", "LAA": "108", "OAK": "133", "SEA": "136",
    "ATL": "144", "MIA": "146", "NYM": "121", "PHI": "143", "WSH": "120",
    "CHC": "112", "CIN": "113", "MIL": "158", "PIT": "134", "STL": "138",
    "ARI": "109", "COL": "115", "LAD": "119", "SD": "135", "SF": "137"
}

for abbr, team_id in teams.items():
    url = f"https://www.mlbstatic.com/team-logos/{team_id}.svg"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(logo_dir / f"{abbr}.svg", 'wb') as f:
                f.write(response.content)
            print(f"✓ {abbr} ロゴをダウンロード")
    except:
        print(f"✗ {abbr} ロゴのダウンロードに失敗")