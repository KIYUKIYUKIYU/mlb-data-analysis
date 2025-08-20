"""
ブルペン詳細統計を取得するクラス
Phase2-2: ブルペン強化（アクティブな投手のみ）
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Dict, List
import json
from datetime import datetime, timedelta
from src.mlb_api_client import MLBApiClient

class BullpenEnhancedStats:
    """ブルペンの詳細統計を取得"""
    
    def __init__(self):
        self.api_client = MLBApiClient()
        self.cache_dir = Path("cache") / "bullpen_stats"
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_enhanced_bullpen_stats(self, team_id: int, season: int = 2024) -> Dict:
        """ブルペンの詳細統計を取得（Phase2-2）
        
        Returns:
            Dict: {
                'era': float,
                'fip': float,
                'xfip': float,
                'whip': float,
                'k_bb_percent': float,
                'war': float,
                'reliever_count': int,
                'closer_name': str,
                'closer_stats': dict,
                'setup_men': list,
                'fatigue_info': dict
            }
        """
        try:
            # キャッシュ確認（短時間のみ有効）
            cache_file = self.cache_dir / f"bullpen_active_{team_id}_{season}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    cached_data = json.load(f)
                    cache_date = datetime.fromisoformat(cached_data.get('date', ''))
                    if datetime.now() - cache_date < timedelta(hours=6):  # 6時間のみ有効
                        return cached_data['stats']
            
            # 直近30日間のカットオフ日
            cutoff_date = datetime.now() - timedelta(days=7)
            
            # ブルペン投手の統計を収集
            bullpen_stats = self.api_client.get_bullpen_stats(team_id, season)
            
            if not bullpen_stats:
                return self._get_default_bullpen_stats()
            
            # アクティブな中継ぎ投手のみを抽出
            active_relievers = []
            
            for pitcher in bullpen_stats:
                stats = pitcher.get('stats', {})
                pitcher_id = pitcher.get('id')
                
                # 基本的な中継ぎ判定
                games_started = stats.get('gamesStarted', 0)
                games_pitched = stats.get('gamesPitched', 0)
                saves = stats.get('saves', 0)
                holds = stats.get('holds', 0)
                ip = float(stats.get('inningsPitched', 0))
                
                # 平均投球回を計算
                avg_ip_per_game = ip / games_pitched if games_pitched > 0 else 0
                
                # 中継ぎ判定条件
                is_reliever = False
                
                # 1. セーブまたはホールドがある
                if saves > 0 or holds > 0:
                    is_reliever = True
                # 2. 10試合以上登板で先発なし
                elif games_pitched >= 10 and games_started == 0:
                    is_reliever = True
                # 3. 平均投球回が2.0未満で10試合以上登板
                elif games_pitched >= 10 and avg_ip_per_game < 2.0:
                    is_reliever = True
                
                if is_reliever:
                    # 直近30日間の登板確認
                    recent_activity = self._check_recent_activity(pitcher_id, cutoff_date)
                    if recent_activity['has_recent_appearance']:
                        pitcher['recent_games'] = recent_activity['games_in_period']
                        active_relievers.append(pitcher)
            
            # 集計変数
            total_ip = 0
            total_er = 0
            total_h = 0
            total_bb = 0
            total_hbp = 0
            total_hr = 0
            total_so = 0
            total_batters = 0
            total_fb = 0
            total_war = 0
            
            reliever_count = len(active_relievers)
            closer_name = None
            closer_stats = {}
            setup_men = []
            
            # 疲労度情報
            fatigue_info = {
                'overworked_relievers': [],
                'consecutive_days': {}
            }
            
            # アクティブな中継ぎ投手のみで統計を集計
            for pitcher in active_relievers:
                stats = pitcher.get('stats', {})
                
                # 統計を集計
                ip = float(stats.get('inningsPitched', 0))
                if ip > 0:
                    total_ip += ip
                    total_er += stats.get('earnedRuns', 0)
                    total_h += stats.get('hits', 0)
                    total_bb += stats.get('baseOnBalls', 0)
                    total_hbp += stats.get('hitByPitch', 0)
                    total_hr += stats.get('homeRuns', 0)
                    total_so += stats.get('strikeOuts', 0)
                    total_batters += stats.get('battersFaced', 0)
                    
                    # フライボール数推定
                    total_fb += ip * 3 * 0.35
                    
                    # WAR（簡易計算）
                    pitcher_war = self._calculate_pitcher_war(stats)
                    total_war += pitcher_war
                
                # クローザー判定
                saves = stats.get('saves', 0)
                if saves >= 5 and pitcher.get('recent_games', 0) >= 5:  # 最近も活動中
                    if not closer_name or saves > closer_stats.get('saves', 0):
                        closer_name = pitcher['name']
                        closer_stats = {
                            'era': float(stats.get('era', 0)),
                            'fip': self._calculate_fip(stats),
                            'saves': saves,
                            'blown_saves': stats.get('blownSaves', 0)
                        }
                
                # セットアッパー判定
                holds = stats.get('holds', 0)
                if holds >= 5 and saves < 5 and pitcher.get('recent_games', 0) >= 5:
                    setup_stats = {
                        'name': pitcher['name'],
                        'era': float(stats.get('era', 0)),
                        'fip': self._calculate_fip(stats),
                        'holds': holds
                    }
                    setup_men.append(setup_stats)
                
                # 疲労度チェック
                if pitcher.get('recent_games', 0) >= 5:  # 直近30日で5試合以上
                    consecutive = pitcher.get('recent_games', 0) / 30 * 7  # 週あたりの登板数
                    if consecutive >= 3:  # 週3回以上は過労気味
                        fatigue_info['overworked_relievers'].append(pitcher['name'])
            
            # セットアッパーをホールド数でソート
            setup_men.sort(key=lambda x: x['holds'], reverse=True)
            
            # 集計値から統計を計算
            if total_ip > 0:
                era = (total_er * 9) / total_ip
                whip = (total_h + total_bb) / total_ip
                fip = ((13 * total_hr) + (3 * (total_bb + total_hbp)) - (2 * total_so)) / total_ip + 3.2
                
                # xFIP計算
                hr_fb_rate = 0.117
                expected_hr = total_fb * hr_fb_rate
                xfip = ((13 * expected_hr) + (3 * (total_bb + total_hbp)) - (2 * total_so)) / total_ip + 3.10
                
                # K-BB%計算
                if total_batters > 0:
                    k_percent = (total_so / total_batters) * 100
                    bb_percent = (total_bb / total_batters) * 100
                    k_bb_percent = k_percent - bb_percent
                else:
                    k_bb_percent = 0.0
            else:
                era = 0.0
                fip = 0.0
                xfip = 0.0
                whip = 0.0
                k_bb_percent = 0.0
            
            result = {
                'era': round(era, 2),
                'fip': round(fip, 2),
                'xfip': round(xfip, 2),
                'whip': round(whip, 2),
                'k_bb_percent': round(k_bb_percent, 1),
                'war': round(total_war, 1),
                'reliever_count': reliever_count,
                'closer_name': closer_name,
                'closer_stats': closer_stats,
                'setup_men': setup_men[:2],  # 上位2名
                'fatigue_info': fatigue_info
            }
            
            # キャッシュに保存
            with open(cache_file, 'w') as f:
                json.dump({
                    'date': datetime.now().isoformat(),
                    'stats': result
                }, f)
            
            return result
            
        except Exception as e:
            print(f"Error getting enhanced bullpen stats: {e}")
            return self._get_default_bullpen_stats()
    
    def _check_recent_activity(self, pitcher_id: int, cutoff_date: datetime) -> Dict:
        """投手の直近の活動を確認"""
        try:
            # 直近のゲームログを取得
            game_logs = self.api_client.get_player_game_logs(pitcher_id, season=2024)
            
            games_in_period = 0
            last_game_date = None
            
            for game in game_logs:
                if 'date' in game:
                    game_date = datetime.strptime(game['date'], '%Y-%m-%d')
                    if game_date >= cutoff_date:
                        games_in_period += 1
                        if not last_game_date or game_date > last_game_date:
                            last_game_date = game_date
            
            return {
                'has_recent_appearance': games_in_period > 0,
                'games_in_period': games_in_period,
                'last_game_date': last_game_date
            }
            
        except Exception:
            # エラー時は簡易的にアクティブとみなす
            return {
                'has_recent_appearance': True,
                'games_in_period': 1,
                'last_game_date': None
            }
    
    def _calculate_fip(self, stats: Dict) -> float:
        """FIPを計算"""
        try:
            hr = stats.get('homeRuns', 0)
            bb = stats.get('baseOnBalls', 0)
            hbp = stats.get('hitByPitch', 0)
            k = stats.get('strikeOuts', 0)
            ip = float(stats.get('inningsPitched', 0))
            
            if ip > 0:
                fip = ((13 * hr) + (3 * (bb + hbp)) - (2 * k)) / ip + 3.2
                return round(fip, 2)
            return 0.0
        except Exception:
            return 0.0
    
    def _calculate_pitcher_war(self, stats: Dict) -> float:
        """投手のWARを簡易計算"""
        try:
            ip = float(stats.get('inningsPitched', 0))
            if ip == 0:
                return 0.0
                
            # FIPベースの簡易WAR計算
            fip = self._calculate_fip(stats)
            league_avg_fip = 4.00
            
            # (リーグ平均FIP - 投手FIP) * イニング / 9 * 調整係数
            war = ((league_avg_fip - fip) * ip / 9) * 0.1
            
            return max(0, war)
            
        except Exception:
            return 0.0
    
    def _get_default_bullpen_stats(self) -> Dict:
        """デフォルトのブルペン統計"""
        return {
            'era': 0.00,
            'fip': 0.00,
            'xfip': 0.00,
            'whip': 0.00,
            'k_bb_percent': 0.0,
            'war': 0.0,
            'reliever_count': 0,
            'closer_name': None,
            'closer_stats': {},
            'setup_men': [],
            'fatigue_info': {
                'overworked_relievers': [],
                'consecutive_days': {}
            }
        }


# テスト実行
if __name__ == "__main__":
    # 古いキャッシュを削除
    import os
    cache_dir = Path("cache") / "bullpen_stats"
    if cache_dir.exists():
        for file in cache_dir.glob("*.json"):
            os.remove(file)
    
    bullpen_stats = BullpenEnhancedStats()
    
    # Yankees のブルペン統計をテスト
    stats = bullpen_stats.get_enhanced_bullpen_stats(147)
    
    print("=== ブルペン詳細統計（アクティブ投手のみ） ===")
    print(f"ERA: {stats['era']} | FIP: {stats['fip']} | xFIP: {stats['xfip']}")
    print(f"WHIP: {stats['whip']} | K-BB%: {stats['k_bb_percent']}%")
    print(f"WAR: {stats['war']}")
    print(f"リリーバー数: {stats['reliever_count']}名（直近30日間に登板）")
    
    if stats['closer_name']:
        print(f"\nクローザー: {stats['closer_name']}")
        if stats['closer_stats']:
            print(f"  ERA: {stats['closer_stats']['era']} | FIP: {stats['closer_stats']['fip']}")
    
    if stats['setup_men']:
        print("\nセットアッパー:")
        for setup in stats['setup_men']:
            print(f"  {setup['name']} - ERA: {setup['era']} | Holds: {setup['holds']}")
    
    if stats['fatigue_info']['overworked_relievers']:
        print(f"\n過労状態: {', '.join(stats['fatigue_info']['overworked_relievers'])}")