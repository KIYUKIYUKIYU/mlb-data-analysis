import sys
from datetime import datetime, timedelta

sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from src.mlb_api_client import MLBApiClient

def format_pitcher_stats(stats):
    if not stats or not stats.get('stats') or not stats['stats'][0].get('splits'):
        return "情報なし"

    s = stats['stats'][0]['splits'][0]['stat']
    era = s.get('era', 'N/A')
    whip = s.get('whip', 'N/A')
    k_per_9 = s.get('strikeoutsPer9Inn', 'N/A')
    bb_per_9 = s.get('walksPer9Inn', 'N/A')

    return f"ERA: {era} | WHIP: {whip} | K/9: {k_per_9} | BB/9: {bb_per_9}"

def format_team_hitting_stats(stats):
    if not stats or not stats.get('stats') or not stats['stats'][0].get('splits'):
        return "情報なし"
    s = stats['stats'][0]['splits'][0]['stat']
    avg = s.get('avg', '.000')
    ops = s.get('ops', '.000')
    runs = s.get('runs', 0)
    hr = s.get('homeRuns', 0)
    return f"AVG: {avg} | OPS: {ops} | 得点: {runs} | 本塁打: {hr}"

def format_bullpen_stats(stats):
    if not stats or not stats.get('stats') or not stats['stats'][0].get('splits'):
        return "ERA: N/A | WHIP: N/A"
    s = stats['stats'][0]['splits'][0]['stat']
    era = s.get('era', 'N/A')
    whip = s.get('whip', 'N/A')
    return f"ERA: {era} | WHIP: {whip}"

def main():
    api_client = MLBApiClient()
    season = datetime.now().year
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"--- {tomorrow}の試合データ取得中 ---")

    schedule = api_client.get_schedule(tomorrow)
    if not schedule or not schedule.get('dates'):
        print("指定された日付の試合は見つかりませんでした。")
        return

    for game in schedule['dates'][0]['games']:
        game_time_utc = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        game_time_jst = game_time_utc + timedelta(hours=9)

        away_team = game['teams']['away']['team']
        home_team = game['teams']['home']['team']

        away_team_stats = api_client.get_team_stats(away_team['id'], season)
        home_team_stats = api_client.get_team_stats(home_team['id'], season)
        away_bullpen_stats = api_client.get_team_bullpen_stats(away_team['id'], season)
        home_bullpen_stats = api_client.get_team_bullpen_stats(home_team['id'], season)
        away_ops_5 = api_client.get_recent_games_ops(away_team['id'], season, 5)
        home_ops_5 = api_client.get_recent_games_ops(home_team['id'], season, 5)

        # --- 先発投手データ取得（2025年データがなければ2024年を取得） ---
        away_sp_info = "未定"
        if game['teams']['away'].get('probablePitcher'):
            sp_id = game['teams']['away']['probablePitcher']['id']
            sp_name = game['teams']['away']['probablePitcher']['fullName']
            sp_stats = api_client.get_player_stats(sp_id, season)
            if not sp_stats or not sp_stats.get('stats') or not sp_stats['stats'][0].get('splits'):
                sp_stats = api_client.get_player_stats(sp_id, season - 1) # 前年の成績を取得
            away_sp_info = f"{sp_name}\n({format_pitcher_stats(sp_stats)})"

        home_sp_info = "未定"
        if game['teams']['home'].get('probablePitcher'):
            sp_id = game['teams']['home']['probablePitcher']['id']
            sp_name = game['teams']['home']['probablePitcher']['fullName']
            sp_stats = api_client.get_player_stats(sp_id, season)
            if not sp_stats or not sp_stats.get('stats') or not sp_stats['stats'][0].get('splits'):
                sp_stats = api_client.get_player_stats(sp_id, season - 1) # 前年の成績を取得
            home_sp_info = f"{sp_name}\n({format_pitcher_stats(sp_stats)})"

        print("="*60)
        print(f"**{away_team['name']} @ {home_team['name']}**")
        print(f"開始時刻: {game_time_jst.strftime('%m/%d %H:%M')} (日本時間)")
        print("-"*50)

        print(f"【{away_team['name']}】")
        print(f"**先発**: {away_sp_info}")
        print(f"**中継ぎ陣**: {format_bullpen_stats(away_bullpen_stats)}")
        print(f"**チーム打撃**: {format_team_hitting_stats(away_team_stats)}")
        print(f"過去5試合OPS: {away_ops_5:.3f}")
        print("")

        print(f"【{home_team['name']}】")
        print(f"**先発**: {home_sp_info}")
        print(f"**中継ぎ陣**: {format_bullpen_stats(home_bullpen_stats)}")
        print(f"**チーム打撃**: {format_team_hitting_stats(home_team_stats)}")
        print(f"過去5試合OPS: {home_ops_5:.3f}")
        print("="*60)
        print("\n")

if __name__ == "__main__":
    main()