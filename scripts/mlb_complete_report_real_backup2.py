#!/usr/bin/env python3
"""
MLBレポート生成スクリプト（実データ版）
過去5/10試合のOPSを実際に計算する機能を追加
※重要：必ず2025年のデータのみを使用すること
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import logging
import json
from src.mlb_api_client import MLBApiClient
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
from scripts.batting_quality_stats import BattingQualityStats

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mlb_report.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MLBCompleteReport:
    """完全版MLBレポート生成クラス"""
    
    def __init__(self):
        self.client = MLBApiClient()
        self.stats_collector = EnhancedStatsCollector()
        self.bullpen_stats = BullpenEnhancedStats()
        self.batting_quality = BattingQualityStats()
        self.logger = logging.getLogger(__name__)
    
    def generate_report(self, target_date=None):
        """指定日のレポートを生成"""
        if target_date is None:
            # 日本時間で明日の日付を計算
            japan_tomorrow = datetime.now() + timedelta(days=1)
            # 日本時間の明日の0時に設定
            japan_tomorrow = japan_tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            # MLB時間に変換（14時間前）
            mlb_datetime = japan_tomorrow - timedelta(hours=14)
            target_date = mlb_datetime.strftime('%Y-%m-%d')
        
        self.logger.info(f"Generating report for date: {target_date}")
        
        # スケジュール取得
        schedule = self.client.get_schedule(target_date)
        if not schedule:
            print("スケジュールを取得できませんでした。")
            return
        
        games = []
        for date_info in schedule.get('dates', []):
            games.extend(date_info.get('games', []))
        
        if not games:
            print(f"{target_date}に試合はありません。")
            return
        
        print(f"\n{'='*60}")
        print(f"MLB試合予想レポート - 日本時間 {japan_tomorrow.strftime('%Y/%m/%d')} の試合")
        print(f"{'='*60}\n")
        
        for game in games:
            self._process_game(game)
    
    def _process_game(self, game):
        """各試合の処理"""
        try:
            # 基本情報
            away_team = game['teams']['away']['team']
            home_team = game['teams']['home']['team']
            game_time_utc = datetime.fromisoformat(game['gameDate'].replace('Z', '+00:00'))
            game_time_jst = game_time_utc + timedelta(hours=9)
            
            print(f"\n{'='*60}")
            print(f"**{away_team['name']} @ {home_team['name']}**")
            print(f"開始時刻: {game_time_jst.strftime('%m/%d %H:%M')} (日本時間)")
            print(f"{'='*50}")
            
            # 先発投手情報
            away_pitcher_id = game['teams']['away'].get('probablePitcher', {}).get('id')
            home_pitcher_id = game['teams']['home'].get('probablePitcher', {}).get('id')
            
            # Away Team
            print(f"\n【{away_team['name']}】")
            if away_pitcher_id:
                self._display_pitcher_stats(away_pitcher_id)
            else:
                print("**先発**: 未定")
            
            # ブルペン統計
            self._display_bullpen_stats(away_team['id'])
            
            # チーム打撃統計（改善版）
            self._display_team_batting_stats(away_team['id'])
            
            # Home Team
            print(f"\n【{home_team['name']}】")
            if home_pitcher_id:
                self._display_pitcher_stats(home_pitcher_id)
            else:
                print("**先発**: 未定")
            
            # ブルペン統計
            self._display_bullpen_stats(home_team['id'])
            
            # チーム打撃統計（改善版）
            self._display_team_batting_stats(home_team['id'])
            
            print("\n" + "="*60)
            
        except Exception as e:
            self.logger.error(f"Error processing game: {str(e)}")
            print(f"エラーが発生しました: {str(e)}")
    
    def _display_pitcher_stats(self, pitcher_id):
        """投手統計を表示"""
        try:
            # 基本情報
            player_info = self.client.get_player_info(pitcher_id)
            if not player_info:
                print("投手情報を取得できませんでした")
                return
            
            # 強化統計を取得
            enhanced_stats = self.stats_collector.get_pitcher_enhanced_stats(pitcher_id)
            
            # 基本情報表示
            print(f"**先発**: {player_info['fullName']} ({enhanced_stats['wins']}勝{enhanced_stats['losses']}敗)")
            
            # 統計表示 - 文字列を数値に変換
            era = float(enhanced_stats['era']) if isinstance(enhanced_stats['era'], str) else enhanced_stats['era']
            fip = float(enhanced_stats['fip']) if isinstance(enhanced_stats['fip'], str) else enhanced_stats['fip']
            xfip = float(enhanced_stats['xfip']) if isinstance(enhanced_stats['xfip'], str) else enhanced_stats['xfip']
            whip = float(enhanced_stats['whip']) if isinstance(enhanced_stats['whip'], str) else enhanced_stats['whip']
            k_bb_pct = float(enhanced_stats['k_bb_pct']) if isinstance(enhanced_stats['k_bb_pct'], str) else enhanced_stats['k_bb_pct']
            gb_pct = float(enhanced_stats['gb_pct']) if isinstance(enhanced_stats['gb_pct'], str) else enhanced_stats['gb_pct']
            fb_pct = float(enhanced_stats['fb_pct']) if isinstance(enhanced_stats['fb_pct'], str) else enhanced_stats['fb_pct']
            qs_rate = float(enhanced_stats['qs_rate']) if isinstance(enhanced_stats['qs_rate'], str) else enhanced_stats['qs_rate']
            swstr_pct = float(enhanced_stats['swstr_pct']) if isinstance(enhanced_stats['swstr_pct'], str) else enhanced_stats['swstr_pct']
            babip = float(enhanced_stats['babip']) if isinstance(enhanced_stats['babip'], str) else enhanced_stats['babip']
            
            print(f"ERA: {era:.2f} | FIP: {fip:.2f} | "
                  f"xFIP: {xfip:.2f} | WHIP: {whip:.2f} | "
                  f"K-BB%: {k_bb_pct:.1f}% | "
                  f"GB%: {gb_pct:.1f}% | FB%: {fb_pct:.1f}% | "
                  f"QS率: {qs_rate:.1f}%")
            
            print(f"SwStr%: {swstr_pct:.1f}% | BABIP: {babip:.3f}")
            
            # 対左右成績 - 文字列を数値に変換
            vs_left_avg = float(enhanced_stats['vs_left']['avg']) if isinstance(enhanced_stats['vs_left']['avg'], str) else enhanced_stats['vs_left']['avg']
            vs_left_ops = float(enhanced_stats['vs_left']['ops']) if isinstance(enhanced_stats['vs_left']['ops'], str) else enhanced_stats['vs_left']['ops']
            vs_right_avg = float(enhanced_stats['vs_right']['avg']) if isinstance(enhanced_stats['vs_right']['avg'], str) else enhanced_stats['vs_right']['avg']
            vs_right_ops = float(enhanced_stats['vs_right']['ops']) if isinstance(enhanced_stats['vs_right']['ops'], str) else enhanced_stats['vs_right']['ops']
            
            print(f"対左: {vs_left_avg:.3f} (OPS {vs_left_ops:.3f}) | "
                  f"対右: {vs_right_avg:.3f} (OPS {vs_right_ops:.3f})")
            
        except Exception as e:
            self.logger.error(f"Error displaying pitcher stats: {str(e)}")
            print(f"投手統計の表示エラー: {str(e)}")
    
    def _display_bullpen_stats(self, team_id):
        """ブルペン統計を表示"""
        try:
            bullpen_data = self.bullpen_stats.get_enhanced_bullpen_stats(team_id)
            
            # active_relieversの数を使用
            reliever_count = len(bullpen_data.get('active_relievers', []))
            
            print(f"\n**中継ぎ陣** ({reliever_count}名):")
            print(f"ERA: {bullpen_data['era']} | FIP: {bullpen_data['fip']} | "
                  f"xFIP: {bullpen_data['xfip']} | WHIP: {bullpen_data['whip']} | "
                  f"K-BB%: {bullpen_data['k_bb_percent']}%")
            
            # 主要リリーバー
            if bullpen_data.get('closer'):
                fip_value = float(bullpen_data['closer']['fip']) if isinstance(bullpen_data['closer']['fip'], str) else bullpen_data['closer']['fip']
                print(f"CL: {bullpen_data['closer']['name']} (FIP: {fip_value:.2f})")
            
            if bullpen_data.get('setup_men'):
                setup_names = []
                for p in bullpen_data['setup_men']:
                    fip_value = float(p['fip']) if isinstance(p['fip'], str) else p['fip']
                    setup_names.append(f"{p['name']} (FIP: {fip_value:.2f})")
                print(f"SU: {', '.join(setup_names)}")
            
            # 疲労度
            if bullpen_data.get('fatigued_count', 0) > 0:
                print(f"疲労度: 主力{bullpen_data['fatigued_count']}名が連投中")
            
        except Exception as e:
            self.logger.error(f"Error displaying bullpen stats: {str(e)}")
            print(f"ブルペン統計の表示エラー: {str(e)}")
    
    def _display_team_batting_stats(self, team_id):
        """チーム打撃統計を表示（改善版）"""
        try:
            # 必ず2025年のデータを使用
            team_stats = self.client.get_team_stats(team_id, 2025)
            
            # 打撃品質統計（シーズン統計に関係なく取得）
            quality_stats = self.batting_quality.get_team_quality_stats(team_id)
            
            print(f"\n**チーム打撃**:")
            
            if not team_stats:
                # シーズン統計がない場合でも表示できるものを表示
                print("シーズン統計: データなし")
                
                # Barrel%とHard-Hit%は表示可能
                print(f"Barrel%: {quality_stats['barrel_pct']:.1f}% | Hard-Hit%: {quality_stats['hard_hit_pct']:.1f}%")
                
                # 過去試合のOPSは取得可能
                recent_ops_5 = self.client.calculate_team_recent_ops_with_cache(team_id, 5)
                recent_ops_10 = self.client.calculate_team_recent_ops_with_cache(team_id, 10)
                print(f"過去5試合OPS: {recent_ops_5:.3f} | 過去10試合OPS: {recent_ops_10:.3f}")
                return
            
            # シーズン統計がある場合の通常処理
            # 過去試合のOPSを追加
            team_stats['recent_ops_5'] = self.client.calculate_team_recent_ops_with_cache(team_id, 5)
            team_stats['recent_ops_10'] = self.client.calculate_team_recent_ops_with_cache(team_id, 10)
            
            # wOBA計算
            woba_data = self.batting_quality.calculate_woba(team_stats)
            
            # 対左右投手成績（2025年）
            splits = self.client.get_team_splits_vs_pitchers(team_id, 2025)
            
            # 文字列を数値に変換
            avg = float(team_stats.get('avg', 0)) if isinstance(team_stats.get('avg'), str) else team_stats.get('avg', 0)
            ops = float(team_stats.get('ops', 0)) if isinstance(team_stats.get('ops'), str) else team_stats.get('ops', 0)
            runs = int(team_stats.get('runs', 0)) if isinstance(team_stats.get('runs'), str) else team_stats.get('runs', 0)
            home_runs = int(team_stats.get('homeRuns', 0)) if isinstance(team_stats.get('homeRuns'), str) else team_stats.get('homeRuns', 0)
            
            print(f"AVG: {avg:.3f} | OPS: {ops:.3f} | "
                  f"得点: {runs} | 本塁打: {home_runs}")
            
            print(f"wOBA: {woba_data['woba']:.3f} | xwOBA: {woba_data['xwoba']:.3f}")
            
            print(f"Barrel%: {quality_stats['barrel_pct']:.1f}% | Hard-Hit%: {quality_stats['hard_hit_pct']:.1f}%")
            
            # 対左右成績 - 文字列を数値に変換
            vs_left_avg = float(splits['vs_left']['avg']) if isinstance(splits['vs_left']['avg'], str) else splits['vs_left']['avg']
            vs_left_ops = float(splits['vs_left']['ops']) if isinstance(splits['vs_left']['ops'], str) else splits['vs_left']['ops']
            vs_right_avg = float(splits['vs_right']['avg']) if isinstance(splits['vs_right']['avg'], str) else splits['vs_right']['avg']
            vs_right_ops = float(splits['vs_right']['ops']) if isinstance(splits['vs_right']['ops'], str) else splits['vs_right']['ops']
            
            print(f"対左投手: {vs_left_avg:.3f} (OPS {vs_left_ops:.3f}) | "
                  f"対右投手: {vs_right_avg:.3f} (OPS {vs_right_ops:.3f})")
            
            # 過去の試合OPS（実データ）
            print(f"過去5試合OPS: {team_stats.get('recent_ops_5', 0.700):.3f} | "
                  f"過去10試合OPS: {team_stats.get('recent_ops_10', 0.700):.3f}")
            
        except Exception as e:
            self.logger.error(f"Error displaying team batting stats: {str(e)}")
            print(f"チーム打撃統計の表示エラー: {str(e)}")

def main():
    """メイン関数"""
    report = MLBCompleteReport()
    
    # コマンドライン引数で日付を指定可能
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
        report.generate_report(target_date)
    else:
        # デフォルトは明日の試合
        report.generate_report()

if __name__ == "__main__":
    main()