import requests
from datetime import datetime

# 現在の日付を確認
print(f"現在: {datetime.now()}")

# MLB APIで今日の試合を確認
url = "https://statsapi.mlb.com/api/v1/schedule"
params = {
    "sportId": 1,
    "date": datetime.now().strftime("%Y-%m-%d")
}

response = requests.get(url, params=params)
data = response.json()

print(f"\n本日の試合数: {data.get('totalGames', 0)}")
for date in data.get('dates', []):
    for game in date.get('games', []):
        print(f"{game['teams']['away']['team']['name']} @ {game['teams']['home']['team']['name']}")