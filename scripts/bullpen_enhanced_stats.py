 
"""
ブルペン拡張統計モジュール
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from src.mlb_api_client import MLBApiClient

logger = logging.getLogger(__name__)

class BullpenEnhancedStats:
    """ブルペンの拡張統計を取得するクラス"""

    def __init__(self):
        self.api_client = MLBApiClient()
        self.cache = {}
        self.cache_dir = "cache/bullpen_stats"
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_enhanced_bullpen_stats(self, team_id: int, date: str = None) -> Dict[str, Any]:
        """チームのブルペン拡張統計を取得"""
        try:
            # キャッシュチェック
            cache_file = f"{self.cache_dir}/team_{team_id}_2025.json"
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # チームのロースターを取得
            roster_data = self.api_client.get_team_roster(team_id)

            # レスポンスの形式を確認
            if not roster_data:
                print(f"No roster data for team {team_id}")
                return self._get_default_stats()

            # rosterがdict型の場合、実際のロースターリストを取得
            if isinstance(roster_data, dict):
                roster = roster_data.get('roster', [])
            else:
                roster = roster_data

            # リリーフ投手のみを抽出
            relievers = []
            for player in roster:
                # playerがdict型かチェック
                if not isinstance(player, dict):
                    continue

                position = player.get('position', {})
                if isinstance(position, dict):
                    position_abbr = position.get('abbreviation', '')
                else:
                    position_abbr = str(position)

                if position_abbr == 'P':
                    person = player.get('person', {})
                    if isinstance(person, dict):
                        player_id = person.get('id')
                        player_name = person.get('fullName', 'Unknown')
                    else:
                        continue

                    if player_id:
                        # 2025年の統計を取得
                        stats = self.api_client.get_player_stats_by_season(player_id, 2025)

                        # get_player_stats_by_seasonは直接統計データを返す
                        if stats and isinstance(stats, dict) and len(stats) > 0:
                            # リリーフ投手かどうかチェック（先発登板が少ない）
                            games_started = int(stats.get('gamesStarted', 0) or 0)
                            games_played = int(stats.get('gamesPlayed', 0) or 0)

                            if games_played > 0 and games_started < games_played * 0.5:
                                relievers.append({
                                    'id': player_id,
                                    'name': player_name,
                                    'stats': stats
                                })

            # ブルペン全体の統計を計算
            total_era = 0
            total_innings = 0
            total_strikeouts = 0
            total_walks = 0
            total_hits = 0
            total_hr = 0
            total_games = 0
            total_batters_faced = 0

            active_relievers = []
            closer = None
            setup_men = []
            fatigued_count = 0

            for reliever in relievers:
                stats = reliever['stats']

                # イニング数の変換
                innings_str = stats.get('inningsPitched', '0.0')
                if '.' in str(innings_str):
                    parts = str(innings_str).split('.')
                    innings = float(parts[0]) + (float(parts[1]) / 3.0 if len(parts) > 1 else 0)
                else:
                    innings = float(innings_str)

                if innings > 0:
                    # 基本統計を集計
                    era = float(stats.get('era', '0.00') or '0.00')
                    total_era += era * innings
                    total_innings += innings
                    total_strikeouts += int(stats.get('strikeOuts', 0) or 0)
                    total_walks += int(stats.get('baseOnBalls', 0) or 0)
                    total_hits += int(stats.get('hits', 0) or 0)
                    total_hr += int(stats.get('homeRuns', 0) or 0)
                    total_games += int(stats.get('gamesPlayed', 0) or 0)
                    total_batters_faced += int(stats.get('battersFaced', 0) or 0)

                    # FIPを計算
                    hbp = int(stats.get('hitByPitch', 0) or 0)
                    k = int(stats.get('strikeOuts', 0) or 0)
                    bb = int(stats.get('baseOnBalls', 0) or 0)
                    hr = int(stats.get('homeRuns', 0) or 0)
                    
                    if innings > 0:
                        fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / innings + 3.10
                    else:
                        fip = 0.00

                    active_relievers.append({
                        'id': reliever['id'],
                        'name': reliever['name'],
                        'era': f"{era:.2f}",
                        'fip': f"{fip:.2f}",
                        'innings': innings,
                        'saves': int(stats.get('saves', 0) or 0),
                        'holds': int(stats.get('holds', 0) or 0)
                    })

                    # 役割を判定
                    saves = int(stats.get('saves', 0) or 0)
                    holds = int(stats.get('holds', 0) or 0)

                    if saves >= 5 and not closer:
                        closer = {
                            'id': reliever['id'],
                            'name': reliever['name'],
                            'fip': f"{fip:.2f}"
                        }
                    elif holds >= 5 and len(setup_men) < 2:
                        setup_men.append({
                            'id': reliever['id'],
                            'name': reliever['name'],
                            'fip': f"{fip:.2f}"
                        })

                    # 疲労度チェック（簡易版）
                    games = int(stats.get('gamesPlayed', 0) or 0)
                    if games > 30:  # 半分以上の試合に登板
                        fatigued_count += 1

            # 全体統計を計算
            if total_innings > 0:
                bullpen_era = total_era / total_innings
                bullpen_whip = (total_walks + total_hits) / total_innings
                k9 = (total_strikeouts / total_innings * 9)
                bb9 = (total_walks / total_innings * 9)
                hr9 = (total_hr / total_innings * 9)
                
                # FIPを計算
                bullpen_fip = ((13 * total_hr) + (3 * total_walks) - (2 * total_strikeouts)) / total_innings + 3.10

                # K-BB%
                if total_batters_faced > 0:
                    k_rate = total_strikeouts / total_batters_faced
                    bb_rate = total_walks / total_batters_faced
                    k_bb_percent = (k_rate - bb_rate) * 100
                else:
                    k_bb_percent = 0.0
            else:
                bullpen_era = 0.00
                bullpen_whip = 0.00
                bullpen_fip = 0.00
                k_bb_percent = 0.0

            # xFIP計算（HR/FBを11%と仮定）
            fb_pct = 35.0  # 仮定値
            if total_innings > 0:
                hr9 = (total_hr / total_innings * 9)
                bb9 = (total_walks / total_innings * 9)
                k9 = (total_strikeouts / total_innings * 9)
                hr9_expected = (fb_pct / 100) * 0.11 * 9
                bullpen_xfip = ((13 * hr9_expected + 3 * bb9 - 2 * k9) / 9) + 3.10
            else:
                bullpen_xfip = 0.00

            result = {
                'era': f"{bullpen_era:.2f}",
                'fip': f"{bullpen_fip:.2f}",
                'xfip': f"{bullpen_xfip:.2f}",
                'whip': f"{bullpen_whip:.2f}",
                'k_bb_percent': f"{k_bb_percent:.1f}",
                'active_relievers': active_relievers,
                'closer': closer,
                'setup_men': setup_men,
                'fatigued_count': fatigued_count
            }

            # キャッシュに保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=True)

            return result

        except Exception as e:
            print(f"ブルペン統計の計算中にエラーが発生: {e}")
            return self._get_default_stats()

    def _get_default_stats(self):
        """デフォルトの統計を返す"""
        return {
            'era': '0.00',
            'fip': '0.00',
            'xfip': '0.00',
            'whip': '0.00',
            'k_bb_percent': '0.0',
            'active_relievers': [],
            'closer': None,
            'setup_men': [],
            'fatigued_count': 0
        }


# テスト用
if __name__ == "__main__":
    stats_collector = BullpenEnhancedStats()

    # Yankees (147)のブルペン統計をテスト
    yankees_bullpen = stats_collector.get_enhanced_bullpen_stats(147)
    print("Yankees bullpen stats:")
    print(f"ERA: {yankees_bullpen['era']}")
    print(f"FIP: {yankees_bullpen['fip']}")
    print(f"Active relievers: {len(yankees_bullpen['active_relievers'])}")
    if yankees_bullpen['closer']:
        print(f"Closer: {yankees_bullpen['closer']['name']}")