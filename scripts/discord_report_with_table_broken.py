 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Discord Report with Table Image - 表画像付きレポート
テキストと表画像の両方をDiscordに送信

実行: python -m scripts.discord_report_with_table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from src.mlb_api_client import MLBApiClient
from src.discord_client import DiscordClient
import time
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.font_manager import FontProperties
import requests
from dotenv import load_dotenv

class DiscordReportWithTable:
    def __init__(self):
        self.client = MLBApiClient()
        self.discord_client = DiscordClient()
        self.jst = pytz.timezone('Asia/Tokyo')
        self.est = pytz.timezone('US/Eastern')
        self.pbp_cache = {}
        
    def get_complete_pitcher_stats(self, pitcher_id, pitcher_name, season):
        """投手の完全統計を取得"""
        try:
            response = self.client._make_request(
                f"people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
            )
            
            if not response or not response.get('stats'):
                return None
                
            season_stats = response['stats'][0].get('splits', [])
            if not season_stats:
                return None
                
            stats = season_stats[0]['stat']
            
            # FIP計算
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', '0'))
            
            fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2 if ip > 0 else 0
            
            # K%, BB%計算
            batters_faced = stats.get('battersFaced', 0)
            k_pct = (k / batters_faced * 100) if batters_faced > 0 else 0
            bb_pct = (bb / batters_faced * 100) if batters_faced > 0 else 0
            
            # QS率計算（省略）
            qs_rate = 'N/A'
            
            # GB%, FB%計算（省略）
            gb_pct = 'N/A'
            fb_pct = 'N/A'
            
            # 対左右成績（省略）
            vs_left = 'N/A'
            vs_right = 'N/A'
            
            return {
                'name': pitcher_name,
                'wins': stats.get('wins', 0),
                'losses': stats.get('losses', 0),
                'era': stats.get('era', 'N/A'),
                'fip': f"{fip:.2f}" if fip > 0 else 'N/A',
                'whip': stats.get('whip', 'N/A'),
                'k_pct': f"{k_pct:.1f}%",
                'bb_pct': f"{bb_pct:.1f}%",
                'k_bb': f"{k_pct - bb_pct:.1f}%",
                'qs_rate': qs_rate,
                'gb_pct': gb_pct,
                'fb_pct': fb_pct,
                'vs_left': vs_left,
                'vs_right': vs_right
            }
        except:
            return None
            
    def get_team_batting_stats(self, team_id, season):
        """チームの打撃統計を取得"""
        try:
            response = self.client._make_request(
                f"teams/{team_id}/stats?season={season}&stats=season&group=hitting"
            )
            
            if not response or not response.get('stats'):
                return None
                
            if response['stats'] and response['stats'][0].get('splits'):
                stats = response['stats'][0]['splits'][0]['stat']
            else:
                return None
            
            # 過去5/10試合のOPS
            recent_5_ops = self._get_team_recent_ops(team_id, season, 5)
            recent_10_ops = self._get_team_recent_ops(team_id, season, 10)
            
            return {
                'avg': stats.get('avg', '.000'),
                'ops': stats.get('ops', '.000'),
                'runs': stats.get('runs', 0),
                'hr': stats.get('homeRuns', 0),
                'recent_5_ops': recent_5_ops,
                'recent_10_ops': recent_10_ops
            }
        except:
            return None
            
    def _get_team_recent_ops(self, team_id, season, games_count):
        """チームの最近N試合のOPSを計算"""
        try:
            # 過去30日間の全試合を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
            schedule = self.client._make_request(
                f"schedule?sportId=1&startDate={start_date.strftime('%Y-%m-%d')}&endDate={end_date.strftime('%Y-%m-%d')}"
            )
            
            if not schedule or not schedule.get('dates'):
                return 'N/A'
                
            # 終了した試合を新しい順に取得
            completed_games = []
            for date in reversed(schedule.get('dates', [])):
                for game in date.get('games', []):
                    # 指定チームが関わる試合か確認
                    if (game['teams']['away']['team']['id'] == team_id or 
                        game['teams']['home']['team']['id'] == team_id):
                        
                        if game['status']['abstractGameState'] == 'Final':
                            completed_games.append({
                                'gamePk': game['gamePk'],
                                'is_home': game['teams']['home']['team']['id'] == team_id
                            })
                            
                        if len(completed_games) >= games_count:
                            break
                            
                if len(completed_games) >= games_count:
                    break
                    
            if not completed_games:
                return 'N/A'
                
            # 各試合のチーム打撃成績を集計
            total_ab = 0
            total_h = 0
            total_bb = 0
            total_hbp = 0
            total_sf = 0
            total_2b = 0
            total_3b = 0
            total_hr = 0
            
            for game_info in completed_games[:games_count]:
                boxscore = self.client._make_request(f"game/{game_info['gamePk']}/boxscore")
                
                if boxscore and 'teams' in boxscore:
                    # 自チームのデータを取得
                    side = 'home' if game_info['is_home'] else 'away'
                    team_data = boxscore['teams'][side]
                    
                    if 'teamStats' in team_data and 'batting' in team_data['teamStats']:
                        batting = team_data['teamStats']['batting']
                        
                        ab = batting.get('atBats', 0)
                        h = batting.get('hits', 0)
                        bb = batting.get('baseOnBalls', 0)
                        hbp = batting.get('hitByPitch', 0)
                        sf = batting.get('sacFlies', 0)
                        doubles = batting.get('doubles', 0)
                        triples = batting.get('triples', 0)
                        hr = batting.get('homeRuns', 0)
                        
                        total_ab += ab
                        total_h += h
                        total_bb += bb
                        total_hbp += hbp
                        total_sf += sf
                        total_2b += doubles
                        total_3b += triples
                        total_hr += hr
                        
            # OPS計算
            if total_ab > 0:
                # 単打数 = 安打 - (二塁打 + 三塁打 + 本塁打)
                singles = total_h - (total_2b + total_3b + total_hr)
                # 塁打数
                total_bases = singles + (2 * total_2b) + (3 * total_3b) + (4 * total_hr)
                
                # 打席数
                pa = total_ab + total_bb + total_hbp + total_sf
                
                if pa > 0:
                    obp = (total_h + total_bb + total_hbp) / pa
                    slg = total_bases / total_ab
                    ops = obp + slg
                    return f"{ops:.3f}"
                    
            return 'N/A'
                
        except Exception as e:
            return 'N/A'
            
    def get_team_bullpen_stats(self, team_id, season):
        """チームの中継ぎ陣統計を取得"""
        try:
            roster = self.client._make_request(f"teams/{team_id}/roster?rosterType=active")
            
            if not roster or not roster.get('roster'):
                return None
                
            bullpen_stats = {
                'total_ip': 0,
                'total_er': 0,
                'total_h': 0,
                'total_bb': 0,
                'total_hbp': 0,
                'total_hr': 0,
                'total_so': 0,
                'total_batters': 0,
                'saves': 0,
                'blown_saves': 0,
                'closer_name': None
            }
            
            relievers_count = 0
            
            for player in roster.get('roster', []):
                if player.get('position', {}).get('type') != 'Pitcher':
                    continue
                    
                pitcher_id = player['person']['id']
                pitcher_name = player['person']['fullName']
                
                stats_response = self.client._make_request(
                    f"people/{pitcher_id}/stats?stats=season&season={season}&group=pitching"
                )
                
                if not stats_response or not stats_response.get('stats'):
                    continue
                    
                season_stats = stats_response['stats'][0].get('splits', [])
                if not season_stats:
                    continue
                    
                stats = season_stats[0]['stat']
                
                if stats.get('gamesStarted', 0) == 0 and stats.get('gamesPlayed', 0) > 0:
                    relievers_count += 1
                    
                    ip = float(stats.get('inningsPitched', '0'))
                    bullpen_stats['total_ip'] += ip
                    bullpen_stats['total_er'] += stats.get('earnedRuns', 0)
                    bullpen_stats['total_h'] += stats.get('hits', 0)
                    bullpen_stats['total_bb'] += stats.get('baseOnBalls', 0)
                    bullpen_stats['total_hbp'] += stats.get('hitByPitch', 0)
                    bullpen_stats['total_hr'] += stats.get('homeRuns', 0)
                    bullpen_stats['total_so'] += stats.get('strikeOuts', 0)
                    bullpen_stats['total_batters'] += stats.get('battersFaced', 0)
                    
                    saves = stats.get('saves', 0)
                    blown_saves = stats.get('blownSaves', 0)
                    bullpen_stats['saves'] += saves
                    bullpen_stats['blown_saves'] += blown_saves
                    
                    if saves >= 10:
                        bullpen_stats['closer_name'] = pitcher_name
                        
            if bullpen_stats['total_ip'] > 0:
                era = (bullpen_stats['total_er'] * 9) / bullpen_stats['total_ip']
                whip = (bullpen_stats['total_bb'] + bullpen_stats['total_h']) / bullpen_stats['total_ip']
                fip = ((13 * bullpen_stats['total_hr']) + 
                       (3 * (bullpen_stats['total_bb'] + bullpen_stats['total_hbp'])) - 
                       (2 * bullpen_stats['total_so'])) / bullpen_stats['total_ip'] + 3.2
                
                return {
                    'relievers_count': relievers_count,
                    'era': f"{era:.2f}",
                    'fip': f"{fip:.2f}",
                    'whip': f"{whip:.2f}",
                    'saves': bullpen_stats['saves'],
                    'blown_saves': bullpen_stats['blown_saves'],
                    'closer': bullpen_stats['closer_name']
                }
            else:
                return None
                
        except:
            return None
            
    def create_game_table(self, game_data, filename):
        """試合データの表を画像として作成"""
        # 日本語フォント対応
        plt.rcParams['font.family'] = ['DejaVu Sans', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
        
        fig, ax = plt.subplots(figsize=(14, 12))
        ax.axis('off')
        
        # タイトル
        game_time = datetime.fromisoformat(game_data['gameDate'].replace('Z', '+00:00'))
        jst_time = game_time.astimezone(self.jst)
        title = f"{game_data['away_team']} @ {game_data['home_team']}"
        subtitle = f"{jst_time.strftime('%Y/%m/%d %H:%M')} JST"
        
        fig.text(0.5, 0.95, title, ha='center', fontsize=20, weight='bold')
        fig.text(0.5, 0.91, subtitle, ha='center', fontsize=14)
        
        # データ準備
        headers = ['', game_data['away_team'], game_data['home_team']]
        
        # 先発投手データ
        away_p = game_data.get('away_pitcher', {})
        home_p = game_data.get('home_pitcher', {})
        
        pitcher_rows = [
            ['Starting Pitcher', 
             f"{away_p.get('name', 'TBD')} ({away_p.get('wins', 0)}-{away_p.get('losses', 0)})" if away_p else 'TBD',
             f"{home_p.get('name', 'TBD')} ({home_p.get('wins', 0)}-{home_p.get('losses', 0)})" if home_p else 'TBD'],
            ['ERA', 
             str(away_p.get('era', 'N/A')) if away_p else 'N/A', 
             str(home_p.get('era', 'N/A')) if home_p else 'N/A'],
            ['FIP', 
             str(away_p.get('fip', 'N/A')) if away_p else 'N/A', 
             str(home_p.get('fip', 'N/A')) if home_p else 'N/A'],
            ['WHIP', 
             str(away_p.get('whip', 'N/A')) if away_p else 'N/A', 
             str(home_p.get('whip', 'N/A')) if home_p else 'N/A'],
            ['K-BB%', 
             str(away_p.get('k_bb', 'N/A')) if away_p else 'N/A', 
             str(home_p.get('k_bb', 'N/A')) if home_p else 'N/A'],
        ]
        
        # 中継ぎ陣データ
        away_bp = game_data.get('away_bullpen', {})
        home_bp = game_data.get('home_bullpen', {})
        
        bullpen_rows = [
            ['Bullpen', '', ''],
            ['ERA', 
             str(away_bp.get('era', 'N/A')) if away_bp else 'N/A', 
             str(home_bp.get('era', 'N/A')) if home_bp else 'N/A'],
            ['FIP', 
             str(away_bp.get('fip', 'N/A')) if away_bp else 'N/A', 
             str(home_bp.get('fip', 'N/A')) if home_bp else 'N/A'],
            ['WHIP', 
             str(away_bp.get('whip', 'N/A')) if away_bp else 'N/A', 
             str(home_bp.get('whip', 'N/A')) if home_bp else 'N/A'],
            ['Closer', 
             str(away_bp.get('closer', 'N/A')) if away_bp and away_bp.get('closer') else 'N/A',
             str(home_bp.get('closer', 'N/A')) if home_bp and home_bp.get('closer') else 'N/A'],
        ]
        
        # チーム打撃データ
        away_b = game_data.get('away_team_batting', {})
        home_b = game_data.get('home_team_batting', {})
        
        batting_rows = [
            ['Team Batting', '', ''],
            ['AVG', 
             str(away_b.get('avg', 'N/A')) if away_b else 'N/A', 
             str(home_b.get('avg', 'N/A')) if home_b else 'N/A'],
            ['OPS', 
             str(away_b.get('ops', 'N/A')) if away_b else 'N/A', 
             str(home_b.get('ops', 'N/A')) if home_b else 'N/A'],
            ['Runs', 
             str(away_b.get('runs', 0)) if away_b else '0', 
             str(home_b.get('runs', 0)) if home_b else '0'],
            ['HR', 
             str(away_b.get('hr', 0)) if away_b else '0', 
             str(home_b.get('hr', 0)) if home_b else '0'],
            ['Last 5 OPS', 
             str(away_b.get('recent_5_ops', 'N/A')) if away_b else 'N/A', 
             str(home_b.get('recent_5_ops', 'N/A')) if home_b else 'N/A'],
            ['Last 10 OPS', 
             str(away_b.get('recent_10_ops', 'N/A')) if away_b else 'N/A', 
             str(home_b.get('recent_10_ops', 'N/A')) if home_b else 'N/A'],
        ]
        
        # 全データを結合
        all_rows = pitcher_rows + [['']*3] + bullpen_rows + [['']*3] + batting_rows
        
        # テーブル作成
        table = ax.table(cellText=all_rows, colLabels=headers,
                        cellLoc='center', loc='center',
                        colWidths=[0.25, 0.375, 0.375])
        
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.2)
        
        # スタイル設定
        for i in range(len(headers)):
            table[(0, i)].set_facecolor('#2E5090')
            table[(0, i)].set_text_props(weight='bold', color='white')
            
        # セクションヘッダーのスタイル
        section_rows = [1, 7, 13]  # Starting Pitcher, Bullpen, Team Batting
        for row in section_rows:
            if row <= len(all_rows):
                for col in range(3):
                    table[(row, col)].set_facecolor('#E8E8E8')
                    table[(row, col)].set_text_props(weight='bold')
        
        # 枠線を太くする
        for key, cell in table.get_celld().items():
            cell.set_linewidth(1.5)
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        
    def format_game_message(self, game_data):
        """1試合のメッセージを作成（順番変更版）"""
        game_time = datetime.fromisoformat(game_data['gameDate'].replace('Z', '+00:00'))
        jst_time = game_time.astimezone(self.jst)
        
        message = f"**{game_data['away_team']} @ {game_data['home_team']}**\n"
        message += f"開始時刻: {jst_time.strftime('%m/%d %H:%M')} (日本時間)\n"
        message += "="*50 + "\n\n"
        
        # Away Team
        message += f"**【{game_data['away_team']}】**\n\n"
        
        # 1. 先発投手
        if game_data.get('away_pitcher'):
            p = game_data['away_pitcher']
            message += f"**先発**: {p['name']} ({p['wins']}勝{p['losses']}敗)\n"
            message += f"ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']} | K-BB%: {p['k_bb']} | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}% | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}% | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}%\n\n"
        else:
            message += "**先発**: 未定\n\n"
            
        # 2. 中継ぎ陣
        if game_data.get('away_bullpen'):
            bp = game_data['away_bullpen']
            message += f"**中継ぎ陣** ({bp['relievers_count']}名):\n"
            message += f"ERA: {bp['era']} | FIP: {bp['fip']} | WHIP: {bp['whip']}\n"
            if bp['closer']:
                message += f"CL: {bp['closer']}\n"
            message += "\n"
            
        # 3. チーム打撃
        if game_data.get('away_team_batting'):
            b = game_data['away_team_batting']
            message += f"**チーム打撃**:\n"
            message += f"AVG: {b['avg']} | OPS: {b['ops']} | 得点: {b['runs']} | 本塁打: {b['hr']}\n"
            message += f"過去5試合OPS: {b['recent_5_ops']} | 過去10試合OPS: {b['recent_10_ops']}\n"
                
        message += "\n"
        
        # Home Team（同じ順番で）
        message += f"**【{game_data['home_team']}】**\n\n"
        
        # 1. 先発投手
        if game_data.get('home_pitcher'):
            p = game_data['home_pitcher']
            message += f"**先発**: {p['name']} ({p['wins']}勝{p['losses']}敗)\n"
            message += f"ERA: {p['era']} | FIP: {p['fip']} | WHIP: {p['whip']} | K-BB%: {p['k_bb']} | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}% | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}% | GB%: {p.get('gb_percent', 'N/A')}% | FB%: {p.get('fb_percent', 'N/A')}%\n\n"
        else:
            message += "**先発**: 未定\n\n"
            
        # 2. 中継ぎ陣
        if game_data.get('home_bullpen'):
            bp = game_data['home_bullpen']
            message += f"**中継ぎ陣** ({bp['relievers_count']}名):\n"
            message += f"ERA: {bp['era']} | FIP: {bp['fip']} | WHIP: {bp['whip']}\n"
            if bp['closer']:
                message += f"CL: {bp['closer']}\n"
            message += "\n"
            
        # 3. チーム打撃
        if game_data.get('home_team_batting'):
            b = game_data['home_team_batting']
            message += f"**チーム打撃**:\n"
            message += f"AVG: {b['avg']} | OPS: {b['ops']} | 得点: {b['runs']} | 本塁打: {b['hr']}\n"
            message += f"過去5試合OPS: {b['recent_5_ops']} | 過去10試合OPS: {b['recent_10_ops']}\n"
                
        message += "\n" + "="*50
        
        return message
        
    def send_with_image(self, text, image_path):
        """テキストと画像をDiscordに送信"""
        load_dotenv()
        webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        
        if not webhook_url:
            print("Discord Webhook URLが設定されていません")
            return
            
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/png')}
                data = {'content': text}
                
                response = requests.post(webhook_url, files=files, data=data)
                
                if response.status_code == 200:
                    print("  [OK] 画像付きメッセージ送信成功")
                else:
                    print(f"  [NG] 送信失敗: {response.status_code}")
                    
        except Exception as e:
            print(f"  [NG] 画像送信エラー: {str(e)}")
            # 画像なしでテキストのみ送信
            self.discord_client.send_text_message(text)
            
    def run_discord_report(self):
        """Discord配信を実行"""
        print("MLB Discord Report with Table - 表付きレポート")
        print("="*50)
        
        # 明日の試合を取得
        now_jst = datetime.now(self.jst)
        #         tomorrow_est = (now_jst - timedelta(hours=13) + timedelta(days=1)).date()
        tomorrow_est = (now_jst - timedelta(hours=13)).date()  # 日本時間をアメリカ東部時間に変換
        
        print(f"明日({tomorrow_est})の試合を取得中...")
        
        schedule = self.client._make_request(
            f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher,team"
        )
        
        if not schedule or not schedule.get('dates'):
            print("明日の試合はありません")
            self.discord_client.send_text_message("明日の試合はありません")
            return
            
        games_data = []
        
        for date in schedule['dates']:
            for game in date.get('games', []):
                if game['status']['abstractGameState'] != 'Preview':
                    continue
                    
                games_data.append({
                    'gamePk': game['gamePk'],
                    'gameDate': game['gameDate'],
                    'away_team': game['teams']['away']['team']['name'],
                    'home_team': game['teams']['home']['team']['name'],
                    'away_team_id': game['teams']['away']['team']['id'],
                    'home_team_id': game['teams']['home']['team']['id'],
                    'away_pitcher_info': game['teams']['away'].get('probablePitcher', {}),
                    'home_pitcher_info': game['teams']['home'].get('probablePitcher', {})
                })
                
        print(f"\n{len(games_data)}試合を検出。処理を開始します...\n")
        
        # 画像用ディレクトリ作成
        img_dir = "temp_images"
        if not os.path.exists(img_dir):
            os.makedirs(img_dir)
            
        # ヘッダーメッセージ
        header = f"**MLB 明日の試合予定 ({tomorrow_est})**\n"
        header += f"全{len(games_data)}試合の詳細情報\n"
        header += "="*50
        self.discord_client.send_text_message(header)
        time.sleep(2)
        
        # 各試合を処理（テスト用に3試合まで）
        for i, game in enumerate(games_data):
            print(f"試合 {i+1}/{len(games_data)}: {game['away_team']} @ {game['home_team']}")
            
            try:
                # 投手統計取得
                for side in ['away', 'home']:
                    pitcher_info = game[f'{side}_pitcher_info']
                    if pitcher_info and pitcher_info.get('id'):
                        print(f"  {pitcher_info['fullName']}の統計を取得中...")
                        pitcher_stats = self.get_complete_pitcher_stats(
                            pitcher_info['id'], 
                            pitcher_info['fullName'],
                            2025
                        )
                        game[f'{side}_pitcher'] = pitcher_stats
                        
                # チーム打撃統計取得
                print("  チーム打撃統計を取得中...")
                game['away_team_batting'] = self.get_team_batting_stats(game['away_team_id'], 2025)
                game['home_team_batting'] = self.get_team_batting_stats(game['home_team_id'], 2025)
                
                # 中継ぎ陣統計取得
                print("  中継ぎ陣統計を取得中...")
                game['away_bullpen'] = self.get_team_bullpen_stats(game['away_team_id'], 2025)
                game['home_bullpen'] = self.get_team_bullpen_stats(game['home_team_id'], 2025)
                
                # テーブル画像作成
                print("  表画像を作成中...")
                image_filename = f"{img_dir}/game_{i+1:02d}.png"
                self.create_game_table(game, image_filename)
                
                # メッセージ作成
                message = self.format_game_message(game)
                
                # Discord送信（画像付き）
                self.send_with_image(message, image_filename)
                
                print(f"  [OK] 試合 {i+1} 配信完了")
                
                # 画像ファイル削除
                if os.path.exists(image_filename):
                    os.remove(image_filename)
                    
            except Exception as e:
                print(f"  [NG] 試合 {i+1} エラー: {str(e)}")
                import traceback
                traceback.print_exc()
                
            time.sleep(3)  # Discord制限対策
            
        print(f"\n処理完了！")

if __name__ == "__main__":
    # matplotlibが必要
    try:
        import matplotlib
        matplotlib.use('Agg')  # GUIなし環境用
    except ImportError:
        print("matplotlibがインストールされていません。")
        print("以下のコマンドでインストールしてください:")
        print("pip install matplotlib")
        sys.exit(1)
        
    system = DiscordReportWithTable()
    system.run_discord_report()