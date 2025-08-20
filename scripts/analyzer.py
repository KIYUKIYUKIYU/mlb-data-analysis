from datetime import datetime, timedelta

def analyze_bullpen(api_client, team_id, season):
    roster_data = api_client.get_team_roster(team_id)
    if not roster_data or 'roster' not in roster_data:
        return get_default_bullpen_stats()

    relievers = []
    for player in roster_data['roster']:
        if player.get('position', {}).get('code') == '1': # '1' is the code for Pitcher
            stats_data = api_client.get_player_stats(player['person']['id'], season)
            if not stats_data or not stats_data.get('stats'): continue

            pitching_stats = stats_data['stats'][0]['splits'][0]['stat']

            # リリーフ投手の単純な定義：登板数のうち先発が半分以下
            games_pitched = pitching_stats.get('gamesPitched', 0)
            games_started = pitching_stats.get('gamesStarted', 0)
            if games_pitched > 0 and (games_started / games_pitched) <= 0.5:
                 relievers.append(pitching_stats)

    if not relievers:
        return get_default_bullpen_stats()

    # 集計
    total_ip, total_er, total_h, total_bb, total_k, total_bf, total_hr, total_hbp = 0.0, 0, 0, 0, 0, 0, 0, 0
    for stats in relievers:
        ip_str = stats.get('inningsPitched', '0.0')
        ip_val = float(ip_str)
        full_innings = int(ip_val)
        partial_innings = round((ip_val - full_innings) * 10 / 3, 2)
        total_ip += full_innings + partial_innings
        total_er += stats.get('earnedRuns', 0)
        total_h += stats.get('hits', 0)
        total_bb += stats.get('baseOnBalls', 0)
        total_k += stats.get('strikeOuts', 0)
        total_bf += stats.get('battersFaced', 0)
        total_hr += stats.get('homeRuns', 0)
        total_hbp += stats.get('hitByPitch', 0)

    # 計算
    era = (total_er * 9 / total_ip) if total_ip > 0 else 0.0
    whip = (total_h + total_bb) / total_ip if total_ip > 0 else 0.0
    k_bb_percent = ((total_k - total_bb) / total_bf * 100) if total_bf > 0 else 0.0

    # FIP計算（FIP定数はシーズンにより変動するが、ここでは一般的な3.10を使用）
    FIP_CONSTANT = 3.10
    fip = (((13 * total_hr) + (3 * (total_bb + total_hbp)) - (2 * total_k)) / total_ip) + FIP_CONSTANT if total_ip > 0 else 0.0

    return {
        'count': len(relievers), 'era': f"{era:.2f}", 'whip': f"{whip:.2f}", 
        'k_bb_percent': f"{k_bb_percent:.1f}%", 'fip': f"{fip:.2f}", 'xfip': "0.00", 'war': "0.0"
    }

def get_default_bullpen_stats():
    return {'count': 0, 'era': "0.00", 'whip': "0.00", 'k_bb_percent': "0.0%", 'fip': "0.00", 'xfip': "0.00", 'war': "0.0"}


def calculate_recent_ops(api_client, team_id, num_games):
    today = datetime.now()
    games_found = []
    for i in range(30):
        if len(games_found) >= num_games: break
        date_to_check = today - timedelta(days=i)
        date_str = date_to_check.strftime('%Y-%m-%d')
        schedule = api_client.get_schedule(date_str)
        if not schedule or not schedule.get('dates'): continue
        for game in schedule['dates'][0]['games']:
            if len(games_found) >= num_games: break
            if game['status']['codedGameState'] == 'F' and (game['teams']['away']['team']['id'] == team_id or game['teams']['home']['team']['id'] == team_id):
                games_found.append(game['gamePk'])

    if not games_found: return ".000"

    total_h, total_ab, total_bb, total_hbp, total_sf, total_2b, total_3b, total_hr = 0, 0, 0, 0, 0, 0, 0, 0
    for game_pk in games_found:
        game_data = api_client.get_game_feed(game_pk)
        if not game_data: continue
        boxscore = game_data.get('liveData', {}).get('boxscore', {})
        teams_data = boxscore.get('teams', {})
        stats_key = 'home' if teams_data.get('home', {}).get('team', {}).get('id') == team_id else 'away'
        team_stats = teams_data.get(stats_key, {}).get('stats', {}).get('hitting', {})
        if not team_stats: continue
        total_ab += team_stats.get('atBats', 0)
        total_h += team_stats.get('hits', 0)
        total_bb += team_stats.get('walks', 0)
        total_hbp += team_stats.get('hitByPitch', 0)
        total_sf += team_stats.get('sacFlies', 0)
        total_2b += team_stats.get('doubles', 0)
        total_3b += team_stats.get('triples', 0)
        total_hr += team_stats.get('homeRuns', 0)

    pa = total_ab + total_bb + total_hbp + total_sf
    if pa == 0: return ".000"
    obp = (total_h + total_bb + total_hbp) / pa
    if total_ab == 0: return f"{obp:.3f}"
    singles = total_h - (total_2b + total_3b + total_hr)
    total_bases = singles + (total_2b * 2) + (total_3b * 3) + (total_hr * 4)
    slg = total_bases / total_ab
    return f"{obp + slg:.3f}"

def get_advanced_hitting_stats(team_id):
    # 【要実装】この関数内に、wOBA, xwOBA, Barrel%, Hard-Hit% を取得する、あなたの元のコードを実装してください。
    # 今はダミーデータを返します。
    return {'woba': "0.000", 'xwoba': "0.000", 'barrel_pct': "0.0%", 'hard_hit_pct': "0.0%"}