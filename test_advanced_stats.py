 
from src.mlb_api_client import MLBApiClient
import json

client = MLBApiClient()

print("=== 投手統計の確認 ===")
# テスト用投手ID（Kevin Gausman）
pitcher_id = 592332

# 1. sabermetrics統計でxFIPを確認
print("\n1. Sabermetrics Stats (xFIP確認)")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/people/{pitcher_id}/stats",
        params={
            'stats': 'sabermetrics',
            'season': 2025,
            'group': 'pitching'
        }
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('stats') and data['stats']:
            for stat_group in data['stats']:
                if stat_group.get('splits'):
                    saber_stat = stat_group['splits'][0].get('stat', {})
                    print(f"xFIP: {saber_stat.get('xfip', 'Not found')}")
                    print(f"FIP: {saber_stat.get('fip', 'Not found')}")
                    # 他の高度な統計も確認
                    for key, value in saber_stat.items():
                        if 'fip' in key.lower() or 'xfip' in key.lower():
                            print(f"{key}: {value}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50)
print("=== チーム打撃統計の確認 ===")
# テスト用チームID（Blue Jays）
team_id = 141

# 2. チームのsabermetrics統計でxwOBAを確認
print("\n2. Team Sabermetrics Stats (xwOBA確認)")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/teams/{team_id}/stats",
        params={
            'stats': 'sabermetrics',
            'season': 2025,
            'group': 'hitting'
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# 3. チームのexpected統計を確認
print("\n3. Team Expected Stats")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/teams/{team_id}/stats",
        params={
            'stats': 'expected',
            'season': 2025,
            'group': 'hitting'
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")

# 4. チームのseasonAdvanced統計を確認
print("\n4. Team Season Advanced Stats")
try:
    response = client.session.get(
        f"{client.base_url}/api/v1/teams/{team_id}/stats",
        params={
            'stats': 'seasonAdvanced',
            'season': 2025,
            'group': 'hitting'
        }
    )
    if response.status_code == 200:
        data = response.json()
        if data.get('stats') and data['stats']:
            for stat_group in data['stats']:
                if stat_group.get('splits'):
                    adv_stat = stat_group['splits'][0].get('stat', {})
                    print("利用可能な高度な打撃統計:")
                    for key in ['woba', 'xwoba', 'xwOBA', 'wOBA', 'wobacon', 'xwobacon']:
                        if key in adv_stat:
                            print(f"  {key}: {adv_stat[key]}")
                    # 全てのキーを確認
                    print("\n全ての統計項目:")
                    for key, value in adv_stat.items():
                        if 'woba' in key.lower() or 'expected' in key.lower():
                            print(f"  {key}: {value}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*50)
print("=== 利用可能な統計タイプ一覧 ===")
try:
    response = client.session.get(f"{client.base_url}/api/v1/statTypes")
    if response.status_code == 200:
        data = response.json()
        print("\n投手統計タイプ:")
        for stat_type in data[:50]:  # 最初の50個
            name = stat_type.get('name', '')
            if any(term in name.lower() for term in ['fip', 'expected', 'quality']):
                print(f"  - {name}: {stat_type.get('description', '')}")
        
        print("\n打撃統計タイプ:")
        for stat_type in data[:50]:
            name = stat_type.get('name', '')
            if any(term in name.lower() for term in ['woba', 'expected', 'barrel']):
                print(f"  - {name}: {stat_type.get('description', '')}")
except Exception as e:
    print(f"Error: {e}")