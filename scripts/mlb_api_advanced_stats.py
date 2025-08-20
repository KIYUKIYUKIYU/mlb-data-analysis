"""
MLB APIのseasonAdvancedエンドポイントから
GB%/FB%/SwStr%/BABIPを取得する拡張機能
"""

class MLBApiAdvancedStats:
    def __init__(self, mlb_client):
        self.client = mlb_client
        
    def get_pitcher_advanced_stats(self, pitcher_id, season=2025):
        """
        投手の詳細統計を取得
        GB%, FB%, SwStr%, BABIPを含む
        """
        url = f"{self.client.base_url}/people/{pitcher_id}/stats"
        params = {
            'stats': 'seasonAdvanced',
            'season': season,
            'group': 'pitching'
        }
        
        try:
            response = self.client.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('stats') and data['stats']:
                for stat_group in data['stats']:
                    if stat_group.get('splits'):
                        advanced_stats = stat_group['splits'][0].get('stat', {})
                        
                        # 必要なデータを取得
                        balls_in_play = int(advanced_stats.get('ballsInPlay', 0))
                        
                        if balls_in_play > 0:
                            # 打球データ
                            ground_outs = int(advanced_stats.get('groundOuts', 0))
                            ground_hits = int(advanced_stats.get('groundHits', 0))
                            fly_outs = int(advanced_stats.get('flyOuts', 0))
                            fly_hits = int(advanced_stats.get('flyHits', 0))
                            line_outs = int(advanced_stats.get('lineOuts', 0))
                            line_hits = int(advanced_stats.get('lineHits', 0))
                            
                            # GB%, FB%, LD%を計算
                            gb_total = ground_outs + ground_hits
                            fb_total = fly_outs + fly_hits
                            ld_total = line_outs + line_hits
                            
                            gb_percent = (gb_total / balls_in_play) * 100
                            fb_percent = (fb_total / balls_in_play) * 100
                            ld_percent = (ld_total / balls_in_play) * 100
                            
                            # スイングデータ
                            total_swings = int(advanced_stats.get('totalSwings', 0))
                            swing_and_misses = int(advanced_stats.get('swingAndMisses', 0))
                            
                            if total_swings > 0:
                                swstr_percent = (swing_and_misses / total_swings) * 100
                            else:
                                swstr_percent = 0.0
                            
                            # BABIP
                            babip = advanced_stats.get('babip')
                            
                            return {
                                'gb_percent': round(gb_percent, 1),
                                'fb_percent': round(fb_percent, 1),
                                'ld_percent': round(ld_percent, 1),
                                'swstr_percent': round(swstr_percent, 1),
                                'babip': babip,
                                'data_source': 'MLB API seasonAdvanced',
                                'balls_in_play': balls_in_play,
                                'total_swings': total_swings
                            }
                        
        except Exception as e:
            print(f"Error getting advanced stats: {e}")
            
        return None


# enhanced_stats_collector.pyの修正版（該当部分）
def get_pitcher_enhanced_stats_with_advanced(self, pitcher_id):
    """投手の高度な統計を取得（MLB API拡張版）"""
    
    # ... 既存のコード ...
    
    # ===== MLB API seasonAdvanced から GB%/FB%/SwStr%/BABIP を取得 =====
    advanced_api = MLBApiAdvancedStats(self.client)
    advanced_data = advanced_api.get_pitcher_advanced_stats(pitcher_id, 2025)
    
    if advanced_data:
        # 取得成功
        gb_percent = advanced_data['gb_percent']
        fb_percent = advanced_data['fb_percent']
        swstr_percent = advanced_data['swstr_percent']
        babip = advanced_data['babip']
        data_source = " (MLB API)"
    else:
        # 取得失敗時は None
        gb_percent = None
        fb_percent = None
        swstr_percent = None
        babip = stats.get('babip')  # 基本統計から取得を試みる
        data_source = ""
    
    # ... 既存のコードの続き ...
    
    result = {
        'name': f"{player_info.get('people', [{}])[0].get('firstName', '')} {player_info.get('people', [{}])[0].get('lastName', '')}",
        'wins': stats.get('wins', 0) or 0,
        'losses': stats.get('losses', 0) or 0,
        'era': str(stats.get('era', '0.00') or '0.00'),
        'fip': f"{fip:.2f}",
        'xfip': xfip_str,
        'whip': str(stats.get('whip', '0.00') or '0.00'),
        'k_bb_percent': f"{k_bb_percent:.1f}%",
        'qs_rate': f"{qs_rate:.1f}%",
        'gb_percent': f"{gb_percent:.1f}%{data_source}" if gb_percent else None,
        'fb_percent': f"{fb_percent:.1f}%{data_source}" if fb_percent else None,
        'swstr_percent': f"{swstr_percent:.1f}%{data_source}" if swstr_percent else None,
        'babip': babip if babip else None,
        'vs_left': vs_left,
        'vs_right': vs_right,
        'splits_note': splits_note
    }