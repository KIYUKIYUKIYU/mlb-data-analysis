#!/usr/bin/env python3
"""
MLBレポート生成スクリプト（実データ版）- 完全版
- データ信頼性表示付き
- ログ出力抑制（クリーンな出力）
- エンコーディングエラー対策済み
※重要：必ず2025年のデータのみを使用すること
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
from src.mlb_api_client import MLBApiClient
from scripts.enhanced_stats_collector import EnhancedStatsCollector
from scripts.bullpen_enhanced_stats import BullpenEnhancedStats
from scripts.batting_quality_stats import BattingQualityStats

# ロギング設定（ファイルのみに出力、コンソールには出力しない）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='mlb_report.log',
    encoding='utf-8'
)

# 特定モジュールのログレベルを上げて、さらに抑制
logging.getLogger('src.mlb_api_client').setLevel(logging.WARNING)
logging.getLogger('scripts.batting_quality_stats').setLevel(logging.WARNING)
logging.getLogger('scripts.enhanced_stats_collector').setLevel(logging.WARNING)
logging.getLogger('scripts.bullpen_enhanced_stats').setLevel(logging.WARNING)
logging.getLogger('scripts.savant_statcast_fetcher').setLevel(logging.CRITICAL)  # CRITICALに変更

class DataReliabilityChecker:
    """データ信頼性チェッククラス"""
    
    def __init__(self):
        self.cache_dir = Path("cache")
        self.now = datetime.now()
    
    def display_simple_reliability(self):
        """シンプルな信頼性表示（1行版）"""
        # 重要なデータの鮮度チェック
        fresh_count = 0
        total_count = 0
        
        important_dirs = ["batting_quality", "bullpen_stats", "recent_ops", "statcast_data"]
        
        for dir_name in important_dirs:
            total_count += 1
            cache_path = self.cache_dir / dir_name
            if cache_path.exists():
                files = list(cache_path.glob("*.json"))
                if files:
                    latest = max(files, key=lambda f: f.stat().st_mtime)
                    age = self.now - datetime.fromtimestamp(latest.stat().st_mtime)
                    if age.days == 0:  # 今日更新されていれば
                        fresh_count += 1
        
        reliability_pct = (fresh_count / total_count * 100) if total_count > 0 else 0
        
        if reliability_pct >= 90:
            status = "[高] データ信頼性: 高"
        elif reliability_pct >= 70:
            status = "[中] データ信頼性: 中"
        else:
            status = "[低] データ信頼性: 要確認"
        
        print(f"{status} ({fresh_count}/{total_count}データが本日更新) | {self.now.strftime('%H:%M')}時点")
        print("-" * 60)
    
    def display_detailed_reliability(self):
        """詳細な信頼性表示"""
        print("【データ更新状況】")
        print("-" * 60)
        
        # データソースごとの状態を確認
        data_status = {
            "MLB API": [],
            "Statcast": [],
        }
        
        # 各キャッシュディレクトリをチェック
        cache_info = {
            "advanced_stats": ("MLB API", "投手統計"),
            "batting_quality": ("MLB API", "打撃統計"),
            "bullpen_stats": ("MLB API", "ブルペン"),
            "recent_ops": ("MLB API", "直近成績"),
            "splits_data": ("MLB API", "対左右"),
            "statcast_data": ("Statcast", "Barrel%/Hard-Hit%")
        }
        
        for dir_name, (source, desc) in cache_info.items():
            cache_path = self.cache_dir / dir_name
            if cache_path.exists():
                files = list(cache_path.glob("*.json"))
                if files:
                    latest = max(files, key=lambda f: f.stat().st_mtime)
                    update_time = datetime.fromtimestamp(latest.stat().st_mtime)
                    age = self.now - update_time
                    
                    if age.total_seconds() < 3600:  # 1時間以内
                        status = "[新]"
                    elif age.days == 0:  # 今日
                        status = "[今日]"
                    else:
                        status = "[古]"
                    
                    time_str = update_time.strftime("%H:%M")
                    file_count = len(files)
                    
                    data_status[source].append(f"{status} {desc} ({time_str}更新, {file_count}ファイル)")
        
        # 表示
        for source, items in data_status.items():
            if items:
                print(f"■ {source}")
                for item in items:
                    print(f"  {item}")
        
        print("-" * 60)

class MLBCompleteReport:
    """完全版MLBレポート生成クラス（データ信頼性表示付き）"""
    
    def __init__(self):
        self.client = MLBApiClient()
        self.stats_collector = EnhancedStatsCollector()
        self.bullpen_stats = BullpenEnhancedStats()
        self.batting_quality = BattingQualityStats()
        self.reliability_checker = DataReliabilityChecker()
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
        else:
            japan_tomorrow = datetime.strptime(target_date, '%Y-%m-%d') + timedelta(hours=14)
        
        self.logger.info(f"Generating report for date: {target_date}")
        
        print(f"\n{'='*60}")
        print(f"MLB試合予想レポート - 日本時間 {japan_tomorrow.strftime('%Y/%m/%d')} の試合")
        print(f"{'='*60}")
        
        # データ信頼性を表示
        print()
        self.reliability_checker.display_simple_reliability()
        print()
        
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
    
    def _safe_float(self, value, default=0.0):
        """文字列や数値を安全にfloatに変換"""
        try:
            if value is None:
                return default
            if isinstance(value, str):
                # %記号を除去
                cleaned = value.replace('%', '').strip()
                return float(cleaned) if cleaned else default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_name(self, name):
        """名前を安全にASCII文字に変換"""
        try:
            # 特殊文字の置換
            replacements = {
                'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
                'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a', 'ã': 'a',
                'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
                'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o', 'õ': 'o',
                'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
                'ñ': 'n', 'ç': 'c'
            }
            for old, new in replacements.items():
                name = name.replace(old, new)
            # それでも残る非ASCII文字を除去
            return name.encode('ascii', 'ignore').decode('ascii')
        except:
            return name
    
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
            era = self._safe_float(enhanced_stats.get('era', '0.00'))
            fip = self._safe_float(enhanced_stats.get('fip', '0.00'))
            xfip = self._safe_float(enhanced_stats.get('xfip', '0.00'))
            whip = self._safe_float(enhanced_stats.get('whip', '0.00'))
            
            # パーセンテージ値の処理
            k_bb_percent_str = enhanced_stats.get('k_bb_percent', '0.0')
            k_bb_percent = self._safe_float(k_bb_percent_str)
            gb_pct = self._safe_float(enhanced_stats.get('gb_percent', '0'))
            fb_pct = self._safe_float(enhanced_stats.get('fb_percent', '0'))
            qs_rate = self._safe_float(enhanced_stats.get('qs_rate', '0'))
            swstr_pct = self._safe_float(enhanced_stats.get('swstr_percent', '0'))
            babip = self._safe_float(enhanced_stats.get('babip', '0'))
            
            # デバッグ出力を削除（コメントアウト）
            # print(f"Debug - Advanced stats for pitcher {pitcher_id}: qualityStarts={enhanced_stats.get('quality_starts', 0)}")
            # print(f"Debug - Pitcher {pitcher_id}: GS={enhanced_stats.get('games_started', 0)}, QS={enhanced_stats.get('quality_starts', 0)}")
            # print(f"Debug - Using API QS rate: {qs_rate:.1f}%")
            
            print(f"ERA: {era:.2f} | FIP: {fip:.2f} | "
                  f"xFIP: {xfip:.2f} | WHIP: {whip:.2f} | "
                  f"K-BB%: {k_bb_percent:.1f}% | "
                  f"GB%: {gb_pct:.1f}% | FB%: {fb_pct:.1f}% | "
                  f"QS率: {qs_rate:.1f}%")
            
            print(f"SwStr%: {swstr_pct:.1f}% | BABIP: {babip:.3f}")
            
            # 対左右成績 - 文字列を数値に変換
            vs_left_avg = self._safe_float(enhanced_stats['vs_left'].get('avg', '.250'))
            vs_left_ops = self._safe_float(enhanced_stats['vs_left'].get('ops', '.700'))
            vs_right_avg = self._safe_float(enhanced_stats['vs_right'].get('avg', '.250'))
            vs_right_ops = self._safe_float(enhanced_stats['vs_right'].get('ops', '.700'))
            
            print(f"対左: {vs_left_avg:.3f} (OPS {vs_left_ops:.3f}) | "
                  f"対右: {vs_right_avg:.3f} (OPS {vs_right_ops:.3f})")
            
        except Exception as e:
            self.logger.error(f"Error displaying pitcher stats: {str(e)}")
            print(f"投手統計の表示エラー: {str(e)}")
    
    def _display_bullpen_stats(self, team_id):
        """ブルペン統計を表示（エンコーディングエラー対策済み）"""
        try:
            bullpen_data = self.bullpen_stats.get_enhanced_bullpen_stats(team_id)
            
            # active_relieversの数を使用
            reliever_count = len(bullpen_data.get('active_relievers', []))
            
            print(f"\n**中継ぎ陣** ({reliever_count}名):")
            print(f"ERA: {bullpen_data['era']} | FIP: {bullpen_data['fip']} | "
                  f"xFIP: {bullpen_data['xfip']} | WHIP: {bullpen_data['whip']} | "
                  f"K-BB%: {bullpen_data['k_bb_percent']}%")
            
            # 主要リリーバー（名前を安全に処理）
            if bullpen_data.get('closer'):
                fip_value = self._safe_float(bullpen_data['closer']['fip'])
                closer_name = self._safe_name(bullpen_data['closer']['name'])
                print(f"CL: {closer_name} (FIP: {fip_value:.2f})")
            
            if bullpen_data.get('setup_men'):
                setup_names = []
                for p in bullpen_data['setup_men']:
                    fip_value = self._safe_float(p['fip'])
                    safe_name = self._safe_name(p['name'])
                    setup_names.append(f"{safe_name} (FIP: {fip_value:.2f})")
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
            # ログ出力を抑制するため、標準エラー出力を一時的に無効化
            import sys
            import io
            old_stderr = sys.stderr
            sys.stderr = io.StringIO()
            try:
                quality_stats = self.batting_quality.get_team_quality_stats(team_id)
            finally:
                sys.stderr = old_stderr
            
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
            avg = self._safe_float(team_stats.get('avg', 0))
            ops = self._safe_float(team_stats.get('ops', 0))
            runs = int(self._safe_float(team_stats.get('runs', 0)))
            home_runs = int(self._safe_float(team_stats.get('homeRuns', 0)))
            
            print(f"AVG: {avg:.3f} | OPS: {ops:.3f} | "
                  f"得点: {runs} | 本塁打: {home_runs}")
            
            print(f"wOBA: {woba_data['woba']:.3f} | xwOBA: {woba_data['xwoba']:.3f}")
            
            print(f"Barrel%: {quality_stats['barrel_pct']:.1f}% | Hard-Hit%: {quality_stats['hard_hit_pct']:.1f}%")
            
            # 対左右成績 - 文字列を数値に変換
            vs_left_avg = self._safe_float(splits['vs_left']['avg'])
            vs_left_ops = self._safe_float(splits['vs_left']['ops'])
            vs_right_avg = self._safe_float(splits['vs_right']['avg'])
            vs_right_ops = self._safe_float(splits['vs_right']['ops'])
            
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
    import argparse
    
    parser = argparse.ArgumentParser(description='MLB試合予想レポート生成（データ信頼性表示付き）')
    parser.add_argument('--date', type=str, help='対象日付 (YYYY-MM-DD形式)')
    parser.add_argument('--check-data', action='store_true', 
                       help='データ信頼性の詳細チェック')
    args = parser.parse_args()
    
    # データチェックモード
    if args.check_data:
        print("=" * 60)
        print("データ信頼性詳細チェック")
        print("=" * 60)
        checker = DataReliabilityChecker()
        checker.display_detailed_reliability()
        sys.exit(0)
    
    # 通常のレポート生成
    report = MLBCompleteReport()
    
    if args.date:
        report.generate_report(args.date)
    else:
        # デフォルトは明日の試合
        report.generate_report()

if __name__ == "__main__":
    main()