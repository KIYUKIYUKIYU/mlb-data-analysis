import sys
from datetime import datetime, timedelta

sys.path.append(r'C:\Users\yfuku\Desktop\mlb-data-analysis')
from src.mlb_api_client import MLBApiClient
from scripts.analyzer import analyze_bullpen, calculate_recent_ops, get_advanced_hitting_stats

def format_pitcher_line(stats):
    if not stats or not stats.get('stats'): return "情報なし"
    s = stats['stats'][0]['splits'][0]['stat']
    wins = s.get('wins', 0)
    losses = s.get('losses', 0)
    era = s.get('era', 'N/A')
    whip = s.get('whip', 'N/A')
    return f"({wins}勝{losses}敗)\nERA: {era} | WHIP: {whip}" # 他の指標は多すぎるため省略

def format_hitting_line(stats):
    if not stats or not stats.get('stats'): return "情報なし"
    s = stats['stats'][0]['splits'][0]['stat']
    return f"AVG: {s.get('avg', '.000')} | OPS: {s.get('ops', '.000')} | 得点: {s.get('runs', 0)} | 本塁打: {s.get('homeRuns', 0)}"

def format_split_line(split_data):
    vsL = ".000"
    vsR = ".000"
    if split_data and split_data.get('stats'):
        for split in split_data['stats'][0]['splits']:
            if split['split']['code'] == 'vl': vsL = split['stat'].get('ops', '.000')
            if split['split']['code'] == 'vr': vsR = split['stat'].get('ops', '.000')
    return f"対左投手: (OPS {vsL}) | 対右投手: (OPS {vsR})"

def main():
    api_client = MLBApiClient()
    season = datetime.now().year
    # JSTで今日の日付から、米国での対象日付（昨日）を算出
    target_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    print(f"--- {target_date} (米国時間) の試合データレポート ---")

    schedule = api_client.get_schedule(target_date)
    if not schedule or not schedule.get('dates'):
        print("対象日付の試合は見つかりませんでした。")
        return

    for game in sorted(schedule['dates'][0]['games'], key=lambda x: x['gameDate']):
        game_time_utc = datetime.strptime(game['gameDate'], '%Y-%m-%dT%H:%M:%SZ')
        game_time_jst = game_time_utc + timedelta(hours=9)

        away = game['teams']['away']['team']
        home = game['teams']['home']['team']

        print("="*60)
        print(f"**{away['name']} @ {home['name']}**")
        print(f"開始時刻: {game_time_jst.strftime('%m/%d %H:%M')} (日本時間)")
        print("-"*50)

        for team in [away, home]:
            team_id = team['id']
            print(f"【{team['name']}】")

            # 先発
            sp_info = "未定"
            sp_team_key = 'away' if team_id == away['id'] else 'home'
            if game['teams'][sp_team_key].get('probablePitcher'):
                sp_id = game['teams'][sp_team_key]['probablePitcher']['id']
                sp_name = game['teams'][sp_team_key]['probablePitcher']['fullName']
                sp_stats = api_client.get_player_stats(sp_id, season)
                if not sp_stats or not sp_stats.get('stats'):
                     sp_stats = api_client.get_player_stats(sp_id, season - 1)
                sp_info = f"{sp_name} {format_pitcher_line(sp_stats)}"
            print(f"**先発**: {sp_info}")

            # 中継ぎ
            bullpen = analyze_bullpen(api_client, team_id, season)
            print(f"**中継ぎ陣** ({bullpen['count']}名):")
            print(f"ERA: {bullpen['era']} | FIP: {bullpen['fip']} | xFIP: {bullpen['xfip']} | WHIP: {bullpen['whip']} | K-BB%: {bullpen['k_bb_percent']} | WAR: {bullpen['war']}")

            # チーム打撃
            hitting = api_client.get_team_stats(team_id, season)
            print(f"**チーム打撃**:")
            print(format_hitting_line(hitting))

            # 高度な打撃指標（ダミー）
            adv_hitting = get_advanced_hitting_stats(team_id)
            print(f"wOBA: {adv_hitting['woba']} | xwOBA: {adv_hitting['xwoba']}")
            print(f"Barrel%: {adv_hitting['barrel_pct']} | Hard-Hit%: {adv_hitting['hard_hit_pct']}")

            # 左右別
            splits = api_client.get_team_hitting_splits(team_id, season)
            print(format_split_line(splits))

            # 最近のOPS
            ops5 = calculate_recent_ops(api_client, team_id, 5)
            ops10 = calculate_recent_ops(api_client, team_id, 10)
            print(f"過去5試合OPS: {ops5} | 過去10試合OPS: {ops10}")
            print("")

        print("="*60)
        print("\n")

if __name__ == "__main__":
    main()