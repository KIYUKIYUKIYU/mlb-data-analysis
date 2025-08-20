 
import sys
sys.path.append('.')
from src.mlb_api_client import MLBApiClient
from datetime import datetime, timedelta

client = MLBApiClient()

# 日本時間の明日
japan_tomorrow = datetime.now() + timedelta(days=1)
japan_tomorrow = japan_tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
mlb_datetime = japan_tomorrow - timedelta(hours=14)
target_date = mlb_datetime.strftime('%Y-%m-%d')

print(f"Checking games for: {target_date}")

schedule = client.get_schedule(target_date)

if schedule:
    for date_info in schedule.get('dates', []):
        for game in date_info.get('games', []):
            away_team = game['teams']['away']['team']['name']
            home_team = game['teams']['home']['team']['name']
            
            # 先発投手情報
            away_pitcher = game['teams']['away'].get('probablePitcher', {})
            home_pitcher = game['teams']['home'].get('probablePitcher', {})
            
            print(f"\n{away_team} @ {home_team}")
            
            if away_pitcher:
                print(f"  Away pitcher: {away_pitcher.get('fullName', 'Unknown')} (ID: {away_pitcher.get('id')})")
            else:
                print(f"  Away pitcher: Not announced")
                
            if home_pitcher:
                print(f"  Home pitcher: {home_pitcher.get('fullName', 'Unknown')} (ID: {home_pitcher.get('id')})")
            else:
                print(f"  Home pitcher: Not announced")