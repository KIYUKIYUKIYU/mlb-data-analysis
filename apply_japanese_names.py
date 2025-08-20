#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
discord_report_with_table_jp.pyに日本語変換を確実に適用
"""
import re
from pathlib import Path

def apply_japanese_conversions():
    """日本語変換を確実に適用"""
    
    file_path = Path("scripts/discord_report_with_table_jp.py")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. format_game_for_discord メソッド内でチーム名を変換
        # home_team = の後に変換を追加
        pattern = r'(home_team = game\[\'teams\'\]\[\'home\'\]\[\'team\'\]\.get\(\'name\', \'Unknown\'\))'
        replacement = r'\1\n        home_team = self.to_japanese_team(home_team)'
        content = re.sub(pattern, replacement, content)
        
        # away_team = の後に変換を追加
        pattern = r'(away_team = game\[\'teams\'\]\[\'away\'\]\[\'team\'\]\.get\(\'name\', \'Unknown\'\))'
        replacement = r'\1\n        away_team = self.to_japanese_team(away_team)'
        content = re.sub(pattern, replacement, content)
        
        # 2. format_pitcher_line メソッド内で投手名を変換
        # pitcher_name取得後に変換を追加
        pattern = r'(pitcher_name = game.*?\.get\(\'fullName\', \'TBD\'\))'
        replacement = r'\1\n                pitcher_name = self.to_japanese_player(pitcher_name)'
        content = re.sub(pattern, replacement, content)
        
        # 3. 日本語変換メソッドが存在しない場合は追加
        if 'def to_japanese_team' not in content:
            # DiscordReportWithTableクラスの最後に追加
            methods = '''
    def to_japanese_team(self, team_name):
        """チーム名を日本語に変換"""
        if hasattr(self, 'name_db') and self.name_db:
            return self.name_db.get_team_name_jp(team_name)
        return team_name
    
    def to_japanese_player(self, player_name):
        """選手名を日本語に変換"""
        if hasattr(self, 'name_db') and self.name_db:
            return self.name_db.get_player_name_jp(player_name)
        return player_name
'''
            # run メソッドの前に挿入
            pattern = r'(\n    def run\(self.*?\):)'
            content = re.sub(pattern, methods + r'\1', content, flags=re.DOTALL)
        
        # 4. 統計用語の日本語化を適用（オプション）
        # ERA → 防御率 など
        stat_replacements = {
            r'\bERA\b': '防御率',
            r'\bWHIP\b': 'WHIP',
            r'\bFIP\b': 'FIP',
            r'K%': '奪三振率',
            r'BB%': '与四球率',
            r'vs L': '対左',
            r'vs R': '対右',
            r'Team BA': 'チーム打率',
            r'Team OPS': 'チームOPS',
            r'Runs/G': '得点/試合',
            r'HR/G': '本塁打/試合'
        }
        
        # レポート文字列内の統計用語を置換
        for eng, jp in stat_replacements.items():
            content = re.sub(f'"{eng}"', f'"{jp}"', content)
            content = re.sub(f"'{eng}'", f"'{jp}'", content)
        
        # ファイルを保存
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("日本語化を適用しました！")
        print("\n確認ポイント:")
        print("✓ チーム名の変換を追加")
        print("✓ 投手名の変換を追加")
        print("✓ 統計用語を日本語化")
        
        # デバッグ用：変換メソッドの存在確認
        if 'to_japanese_team' in content:
            print("✓ to_japanese_team メソッドが存在")
        if 'to_japanese_player' in content:
            print("✓ to_japanese_player メソッドが存在")
            
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()

def verify_json_files():
    """JSONファイルの存在と内容を確認"""
    from pathlib import Path
    import json
    
    data_dir = Path("data")
    if not data_dir.exists():
        print("\n⚠️ dataディレクトリが存在しません！")
        data_dir.mkdir()
        print("dataディレクトリを作成しました")
    
    # チーム名JSONを確認
    team_file = data_dir / "team_names_jp.json"
    if not team_file.exists():
        print("\n⚠️ team_names_jp.json が存在しません！")
        # デフォルトデータを作成
        default_teams = {
            "Detroit Tigers": "タイガース",
            "Tampa Bay Rays": "レイズ",
            "New York Yankees": "ヤンキース",
            "Baltimore Orioles": "オリオールズ",
            "Los Angeles Dodgers": "ドジャース",
            "San Diego Padres": "パドレス",
            # 他のチームも追加...
        }
        with open(team_file, 'w', encoding='utf-8') as f:
            json.dump(default_teams, f, ensure_ascii=False, indent=2)
        print("team_names_jp.json を作成しました")
    
    # 選手名JSONを確認
    player_file = data_dir / "player_names_jp.json"
    if not player_file.exists():
        print("\n⚠️ player_names_jp.json が存在しません！")
        # デフォルトデータを作成
        default_players = {
            "Shohei Ohtani": "大谷翔平",
            "Yoshinobu Yamamoto": "山本由伸",
            # 他の選手も追加...
        }
        with open(player_file, 'w', encoding='utf-8') as f:
            json.dump(default_players, f, ensure_ascii=False, indent=2)
        print("player_names_jp.json を作成しました")

if __name__ == "__main__":
    print("日本語化を適用中...")
    print("=" * 50)
    
    # JSONファイルを確認
    verify_json_files()
    
    # 日本語化を適用
    apply_japanese_conversions()
    
    print("\n実行コマンド:")
    print("python -m scripts.discord_report_with_table_jp")