"""
MLB先発投手データ取得エンドポイントテスター
様々なAPIエンドポイントを試して先発投手情報を取得
"""
import json
from datetime import datetime, timedelta
from src.mlb_api_client import MLBApiClient
import time


class PitcherEndpointTester:
    def __init__(self):
        self.client = MLBApiClient()
        self.results = {}
        
    def test_all_endpoints(self, game_pk: int = None):
        """全てのエンドポイントをテスト"""
        print("="*60)
        print("先発投手取得エンドポイントテスト")
        print("="*60)
        
        # テスト用の試合を取得
        if not game_pk:
            game_pk = self._get_test_game()
            
        if not game_pk:
            print("テスト用の試合が見つかりません")
            return
            
        print(f"\nテスト対象試合ID: {game_pk}")
        print("-"*40)
        
        # 各エンドポイントをテスト
        self._test_basic_schedule(game_pk)
        self._test_hydrate_probable_pitcher(game_pk)
        self._test_hydrate_with_note(game_pk)
        self._test_game_content(game_pk)
        self._test_game_context(game_pk)
        self._test_linescore(game_pk)
        self._test_game_feed(game_pk)
        self._test_preview(game_pk)
        
        # 結果サマリー
        self._print_summary()
        
    def _get_test_game(self) -> int:
        """テスト用の明日の試合を取得"""
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        schedule = self.client._make_request(f"schedule?sportId=1&date={mlb_tomorrow}")
        
        if schedule and schedule.get('dates'):
            return schedule['dates'][0]['games'][0]['gamePk']
        return None
        
    def _test_basic_schedule(self, game_pk: int):
        """基本的なscheduleエンドポイント"""
        print("\n1. 基本schedule API")
        
        # 日付から逆引き
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = self.client._make_request(f"schedule?sportId=1&date={mlb_tomorrow}")
        
        if data and data.get('dates'):
            for game in data['dates'][0]['games']:
                if game['gamePk'] == game_pk:
                    away = game['teams']['away'].get('probablePitcher', {})
                    home = game['teams']['home'].get('probablePitcher', {})
                    
                    print(f"  Away: {away.get('fullName', '未定')}")
                    print(f"  Home: {home.get('fullName', '未定')}")
                    
                    self.results['basic'] = {
                        'away': away.get('fullName'),
                        'home': home.get('fullName')
                    }
                    break
                    
    def _test_hydrate_probable_pitcher(self, game_pk: int):
        """hydrate=probablePitcherパラメータ"""
        print("\n2. schedule?hydrate=probablePitcher")
        
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = self.client._make_request(
            f"schedule?sportId=1&date={mlb_tomorrow}&hydrate=probablePitcher"
        )
        
        if data and data.get('dates'):
            for game in data['dates'][0]['games']:
                if game['gamePk'] == game_pk:
                    away = game['teams']['away'].get('probablePitcher', {})
                    home = game['teams']['home'].get('probablePitcher', {})
                    
                    print(f"  Away: {away.get('fullName', '未定')}")
                    print(f"  Home: {home.get('fullName', '未定')}")
                    
                    # 追加情報があるか確認
                    if away:
                        print(f"    追加情報: {list(away.keys())}")
                        
                    self.results['hydrate'] = {
                        'away': away.get('fullName'),
                        'home': home.get('fullName')
                    }
                    break
                    
    def _test_hydrate_with_note(self, game_pk: int):
        """hydrate=probablePitcher(note)パラメータ"""
        print("\n3. schedule?hydrate=probablePitcher(note)")
        
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = self.client._make_request(
            f"schedule?sportId=1&date={mlb_tomorrow}&hydrate=probablePitcher(note)"
        )
        
        if data and data.get('dates'):
            for game in data['dates'][0]['games']:
                if game['gamePk'] == game_pk:
                    away = game['teams']['away'].get('probablePitcher', {})
                    home = game['teams']['home'].get('probablePitcher', {})
                    
                    print(f"  Away: {away.get('fullName', '未定')}")
                    if away.get('note'):
                        print(f"    Note: {away['note']}")
                    
                    print(f"  Home: {home.get('fullName', '未定')}")
                    if home.get('note'):
                        print(f"    Note: {home['note']}")
                        
                    self.results['hydrate_note'] = {
                        'away': away.get('fullName'),
                        'home': home.get('fullName')
                    }
                    break
                    
    def _test_game_content(self, game_pk: int):
        """game/{gamePk}/contentエンドポイント"""
        print(f"\n4. game/{game_pk}/content")
        
        data = self.client._make_request(f"game/{game_pk}/content")
        
        if data:
            # 複数の場所をチェック
            locations = [
                "gameData.probablePitchers",
                "preview.probablePitchers",
                "editorial.preview.mlb.probablePitchers"
            ]
            
            for loc in locations:
                parts = loc.split('.')
                temp = data
                for part in parts:
                    if isinstance(temp, dict) and part in temp:
                        temp = temp[part]
                    else:
                        temp = None
                        break
                        
                if temp:
                    print(f"  Found in {loc}:")
                    if isinstance(temp, dict):
                        away = temp.get('away', {})
                        home = temp.get('home', {})
                        print(f"    Away: {away.get('fullName', '未定')}")
                        print(f"    Home: {home.get('fullName', '未定')}")
                        
                        self.results[f'content_{loc}'] = {
                            'away': away.get('fullName'),
                            'home': home.get('fullName')
                        }
                        
    def _test_game_context(self, game_pk: int):
        """game/{gamePk}/contextMetricsエンドポイント"""
        print(f"\n5. game/{game_pk}/contextMetrics")
        
        data = self.client._make_request(f"game/{game_pk}/contextMetrics")
        
        if data:
            print(f"  データ取得成功")
            # contextMetricsに投手情報があるか確認
            if 'game' in data and 'probablePitchers' in data['game']:
                pitchers = data['game']['probablePitchers']
                print(f"    投手情報あり: {pitchers}")
            else:
                print(f"    投手情報なし")
                
    def _test_linescore(self, game_pk: int):
        """game/{gamePk}/linescoreエンドポイント"""
        print(f"\n6. game/{game_pk}/linescore")
        
        data = self.client._make_request(f"game/{game_pk}/linescore")
        
        if data:
            # 試合前の場合、先発投手情報が含まれる可能性
            if 'teams' in data:
                for team in ['away', 'home']:
                    if team in data['teams'] and 'probablePitcher' in data['teams'][team]:
                        pitcher = data['teams'][team]['probablePitcher']
                        print(f"  {team}: {pitcher.get('fullName', '未定')}")
                        
    def _test_game_feed(self, game_pk: int):
        """game/{gamePk}/feed/liveエンドポイント"""
        print(f"\n7. game/{game_pk}/feed/live")
        
        data = self.client._make_request(f"game/{game_pk}/feed/live")
        
        if data and 'gameData' in data:
            probables = data['gameData'].get('probablePitchers', {})
            
            if probables:
                away = probables.get('away', {})
                home = probables.get('home', {})
                
                print(f"  Away: {away.get('fullName', '未定')}")
                print(f"  Home: {home.get('fullName', '未定')}")
                
                self.results['feed_live'] = {
                    'away': away.get('fullName'),
                    'home': home.get('fullName')
                }
                
    def _test_preview(self, game_pk: int):
        """schedule?hydrate=previewパラメータ"""
        print("\n8. schedule?hydrate=preview")
        
        japan_now = datetime.now()
        et_now = japan_now - timedelta(hours=13)
        mlb_tomorrow = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = self.client._make_request(
            f"schedule?sportId=1&date={mlb_tomorrow}&hydrate=preview"
        )
        
        if data and data.get('dates'):
            print(f"  データ取得成功 - preview情報を確認中")
            
    def _print_summary(self):
        """結果サマリーを表示"""
        print("\n" + "="*60)
        print("結果サマリー")
        print("="*60)
        
        success_count = 0
        for endpoint, result in self.results.items():
            if result and (result.get('away') or result.get('home')):
                success_count += 1
                print(f"✅ {endpoint}: Away={result.get('away', '未定')}, Home={result.get('home', '未定')}")
            else:
                print(f"❌ {endpoint}: データなし")
                
        print(f"\n成功率: {success_count}/{len(self.results)} エンドポイント")
        

def main():
    """メイン実行"""
    tester = PitcherEndpointTester()
    
    print("先発投手データ取得のための全エンドポイントをテストします...")
    tester.test_all_endpoints()
    
    print("\n💡 ヒント:")
    print("- 成功したエンドポイントがあれば、それを使用")
    print("- 全て失敗の場合は、時間帯や発表タイミングの問題の可能性")
    

if __name__ == "__main__":
    main()