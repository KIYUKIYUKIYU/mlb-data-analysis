"""
MLBデータ分析システム - 完全版レポート生成
Phase2完成版（2025/06/25）
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any
from datetime import datetime, timedelta
from src.mlb_api_client import MLBApiClient
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.batting_quality_stats import BattingQualityStats
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats

class MLBCompleteReporter:
    def __init__(self):
        self.api_client = MLBApiClient()
        self.stats_collector = EnhancedStatsCollector()
        self.batting_quality = BattingQualityStats()
        self.bullpen_stats = BullpenEnhancedStats()
    
    def get_tomorrow_games(self) -> List[Dict[str, Any]]:
        """明日の試合を取得（日本時間基準）"""
        japan_tomorrow = datetime.now() + timedelta(days=1)
        us_game_date = japan_tomorrow - timedelta(hours=14)
        
        schedule_data = self.api_client.get_schedule(us_game_date.strftime('%Y-%m-%d'))
        if not schedule_data or 'dates' not in schedule_data:
            return []
        
        dates = schedule_data.get('dates', [])
        if not dates:
            return []
        
        games = dates[0].get('games', [])
        return [g for g in games if g['status']['detailedState'] == 'Scheduled']
    
    def _get_handicap(self, team_name: str) -> tuple:
        """ハンデを取得"""
        handicaps = {
            'New York Yankees': 0.4,
            'Baltimore Orioles': -0.4,
        }
        value = handicaps.get(team_name, 0.0)
        if value > 0:
            return value, "もらい"
        elif value < 0:
            return abs(value), "出し"
        else:
            return 0.0, "なし"
    
    def format_game_stats(self, game: Dict[str, Any]) -> str:
        """試合情報を完全フォーマット"""
        teams = game['teams']
        away_team = teams['away']
        home_team = teams['home']
        
        # 日本時間で表示
        game_time = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
        japan_time = game_time + timedelta(hours=9)
        
        output = "=" * 60 + "\n"
        output += f"**{away_team['team']['name']} @ {home_team['team']['name']}**\n"
        output += f"開始時刻: {japan_time.strftime('%m/%d %H:%M')} (日本時間)\n"
        output += "=" * 50 + "\n"
        
        # 両チームの詳細統計
        output += self._format_team_stats(away_team)
        output += self._format_team_stats(home_team)
        output += "=" * 50 + "\n"
        
        return output
    
    def _format_team_stats(self, team_data: Dict) -> str:
        """チーム統計のフォーマット"""
        team_name = team_data['team']['name']
        team_id = team_data['team']['id']
        
        # ハンデ取得
        handicap_value, handicap_type = self._get_handicap(team_name)
        
        output = f"【{team_name}】"
        if handicap_value > 0:
            output += f" ハンデ: {handicap_value:+.1f} ({handicap_type})"
        output += "\n"
        
        # 先発投手情報
        if 'probablePitcher' in team_data:
            pitcher = team_data['probablePitcher']
            pitcher_id = pitcher['id']
            
            # 拡張統計を取得
            pitcher_stats = self.stats_collector.get_pitcher_enhanced_stats(pitcher_id)
            
            output += f"**先発**: {pitcher['fullName']} ({pitcher_stats.get('wins', 0)}勝{pitcher_stats.get('losses', 0)}敗)\n"
            
            # 投手統計行1
            output += f"ERA: {pitcher_stats.get('era', '0.00')} | "
            output += f"FIP: {pitcher_stats.get('fip', '0.00')} | "
            output += f"xFIP: {pitcher_stats.get('xfip', '0.00')} | "
            output += f"WHIP: {pitcher_stats.get('whip', '0.00')} | "
            output += f"K-BB%: {pitcher_stats.get('k_bb_percent', '0.0%')} | "
            output += f"GB%: {pitcher_stats.get('gb_percent', '0.0%')} | "
            output += f"FB%: {pitcher_stats.get('fb_percent', '0.0%')} | "
            output += f"QS率: {pitcher_stats.get('qs_rate', '0.0%')}\n"
            
            # 投手統計行2
            output += f"SwStr%: {pitcher_stats.get('swstr_percent', '0.0%')} | "
            output += f"BABIP: {pitcher_stats.get('babip', '.300')}\n"
            
            # 対左右成績
            vs_left = pitcher_stats.get('vs_left', {})
            vs_right = pitcher_stats.get('vs_right', {})
            output += f"対左: {vs_left.get('avg', '.000')} "
            output += f"(OPS {vs_left.get('ops', '.000')}) | "
            output += f"対右: {vs_right.get('avg', '.000')} "
            output += f"(OPS {vs_right.get('ops', '.000')})\n"
        else:
            output += "**先発**: 未定\n"
        
        # ブルペン詳細統計
        try:
            bullpen_data = self.bullpen_stats.get_enhanced_bullpen_stats(team_id)
            active_count = len(bullpen_data.get('active_relievers', []))
            
            output += f"**中継ぎ陣** ({active_count}名):\n"
            output += f"ERA: {bullpen_data.get('era', '0.00')} | "
            output += f"FIP: {bullpen_data.get('fip', '0.00')} | "
            output += f"xFIP: {bullpen_data.get('xfip', '0.00')} | "
            output += f"WHIP: {bullpen_data.get('whip', '0.00')} | "
            output += f"K-BB%: {bullpen_data.get('k_bb_percent', '0.0')}% | "
            output += f"WAR: {bullpen_data.get('war', '0.0')}\n"
            
            # クローザーとセットアッパー
            if bullpen_data.get('closer'):
                closer = bullpen_data['closer']
                output += f"CL: {closer['name']} (FIP: {closer.get('fip', '0.00')})\n"
            
            if bullpen_data.get('setup_men'):
                setup_names = [f"{s['name']} (FIP: {s.get('fip', '0.00')})" for s in bullpen_data['setup_men'][:2]]
                output += f"SU: {', '.join(setup_names)}\n"
            
            # 疲労度
            fatigued_count = bullpen_data.get('fatigued_count', 0)
            if fatigued_count > 0:
                output += f"疲労度: 主力{fatigued_count}名が連投中\n"
        except Exception as e:
            print(f"ブルペン統計取得エラー: {e}")
            output += "**中継ぎ陣**: データ取得エラー\n"
        
        # チーム打撃統計
        try:
            team_stats = self.api_client.get_team_stats(team_id, 2025)
            if team_stats and 'stats' in team_stats:
                stats_list = team_stats.get('stats', [])
                if stats_list and len(stats_list) > 0:
                    first_stat = stats_list[0]
                    if 'splits' in first_stat and first_stat['splits']:
                        hitting = first_stat['splits'][0].get('stat', {})
                    else:
                        hitting = {}
                else:
                    hitting = {}
            else:
                hitting = {}
            
            output += "**チーム打撃**:\n"
            output += f"AVG: {hitting.get('avg', '.000')} | "
            output += f"OPS: {hitting.get('ops', '.000')} | "
            output += f"得点: {hitting.get('runs', 0)} | "
            output += f"本塁打: {hitting.get('homeRuns', 0)}\n"
            
            # Barrel%とHard-Hit%
            quality_stats = self.batting_quality.get_team_quality_stats(team_id)
            output += f"wOBA: {quality_stats.get('woba', 0.315):.3f} | "
            output += f"xwOBA: {quality_stats.get('xwoba', 0.320):.3f}\n"
            output += f"Barrel%: {quality_stats.get('barrel_pct', 7.5):.1f}% | "
            output += f"Hard-Hit%: {quality_stats.get('hard_hit_pct', 38.5):.1f}%\n"
            
            # 対左右投手成績
            try:
                splits = self.api_client.get_team_splits_vs_pitchers(team_id, 2025)
                vs_left_avg = splits.get('vs_left', {}).get('avg', '.250')
                vs_left_ops = splits.get('vs_left', {}).get('ops', '.700')
                vs_right_avg = splits.get('vs_right', {}).get('avg', '.250')
                vs_right_ops = splits.get('vs_right', {}).get('ops', '.700')
                
                output += f"対左投手: {vs_left_avg} (OPS {vs_left_ops}) | "
                output += f"対右投手: {vs_right_avg} (OPS {vs_right_ops})\n"
            except:
                output += f"対左投手: .250 (OPS .700) | "
                output += f"対右投手: .250 (OPS .700)\n"
            
            # 過去5試合・10試合のOPS
            try:
                recent_ops = self.api_client.calculate_team_recent_ops(team_id)
                output += f"過去5試合OPS: {recent_ops.get('last_5_games', 0.700):.3f} | "
                output += f"過去10試合OPS: {recent_ops.get('last_10_games', 0.700):.3f}\n"
            except:
                output += f"過去5試合OPS: 0.700 | "
                output += f"過去10試合OPS: 0.700\n"
            
        except Exception as e:
            print(f"Error getting team stats: {e}")
            output += "**チーム打撃**: データ取得エラー\n"
        
        return output
    
    def save_discord_format(self, content: str, filename: str = "discord_report.txt"):
        """Discord用フォーマットで保存"""
        chunks = []
        lines = content.split('\n')
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1
            if current_length + line_length > 1900:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        with open(filename, 'w', encoding='utf-8') as f:
            for i, chunk in enumerate(chunks):
                f.write(f"=== Part {i+1}/{len(chunks)} ===\n")
                f.write(chunk)
                f.write("\n\n")
        
        print(f"Discord用レポートを {filename} に保存しました（{len(chunks)}分割）")
        return chunks
    
    def generate_full_report(self):
        """全試合の完全レポートを生成"""
        games = self.get_tomorrow_games()
        
        if not games:
            print("明日の試合はありません。")
            return
        
        japan_tomorrow = datetime.now() + timedelta(days=1)
        full_report = f"MLB試合レポート - {japan_tomorrow.strftime('%Y年%m月%d日')}（日本時間）\n"
        full_report += f"全{len(games)}試合\n\n"
        
        for game in games:
            try:
                game_report = self.format_game_stats(game)
                full_report += game_report + "\n"
                print(game_report)
            except Exception as e:
                import traceback
                print(f"Error processing game: {e}")
                traceback.print_exc()
                continue
        
        # Discord用に保存
        self.save_discord_format(full_report)
        
        # Discord送信（利用可能な場合）
        try:
            if hasattr(self, 'discord_client') and self.discord_client:
                chunks = self.save_discord_format(full_report)
                for chunk in chunks:
                    self.discord_client.send_message(chunk)
        except:
            print("Discord送信メソッドが見つかりません")
        
        return full_report


if __name__ == "__main__":
    reporter = MLBCompleteReporter()
    reporter.generate_full_report()