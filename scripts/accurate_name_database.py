 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Accurate Name Database - 正確な選手名データベース
日本のスポーツメディアで実際に使用されている表記を収録

このデータは以下から収集：
- スポーツナビ
- 日刊スポーツ
- MLB公式日本語サイト
- NHK BS放送
"""

import json
import os
from datetime import datetime

class AccurateNameDatabase:
    def __init__(self):
        self.db_path = "data/player_names_jp.json"
        self.team_db_path = "data/team_names_jp.json"
        self.load_database()
        
    def load_database(self):
        """データベースを読み込む"""
        # チーム名データベース（これは固定）
        self.TEAM_NAMES_OFFICIAL = {
            # アメリカンリーグ東地区
            "Baltimore Orioles": {
                "full": "ボルティモア・オリオールズ",
                "short": "オリオールズ",
                "abbr": "BAL"
            },
            "Boston Red Sox": {
                "full": "ボストン・レッドソックス",
                "short": "レッドソックス",
                "abbr": "BOS"
            },
            "New York Yankees": {
                "full": "ニューヨーク・ヤンキース",
                "short": "ヤンキース",
                "abbr": "NYY"
            },
            "Tampa Bay Rays": {
                "full": "タンパベイ・レイズ",
                "short": "レイズ",
                "abbr": "TB"
            },
            "Toronto Blue Jays": {
                "full": "トロント・ブルージェイズ",
                "short": "ブルージェイズ",
                "abbr": "TOR"
            },
            
            # アメリカンリーグ中地区
            "Chicago White Sox": {
                "full": "シカゴ・ホワイトソックス",
                "short": "ホワイトソックス",
                "abbr": "CWS"
            },
            "Cleveland Guardians": {
                "full": "クリーブランド・ガーディアンズ",
                "short": "ガーディアンズ",
                "abbr": "CLE"
            },
            "Detroit Tigers": {
                "full": "デトロイト・タイガース",
                "short": "タイガース",
                "abbr": "DET"
            },
            "Kansas City Royals": {
                "full": "カンザスシティ・ロイヤルズ",
                "short": "ロイヤルズ",
                "abbr": "KC"
            },
            "Minnesota Twins": {
                "full": "ミネソタ・ツインズ",
                "short": "ツインズ",
                "abbr": "MIN"
            },
            
            # アメリカンリーグ西地区
            "Houston Astros": {
                "full": "ヒューストン・アストロズ",
                "short": "アストロズ",
                "abbr": "HOU"
            },
            "Los Angeles Angels": {
                "full": "ロサンゼルス・エンゼルス",
                "short": "エンゼルス",
                "abbr": "LAA"
            },
            "Oakland Athletics": {
                "full": "オークランド・アスレチックス",
                "short": "アスレチックス",
                "abbr": "OAK"
            },
            "Seattle Mariners": {
                "full": "シアトル・マリナーズ",
                "short": "マリナーズ",
                "abbr": "SEA"
            },
            "Texas Rangers": {
                "full": "テキサス・レンジャーズ",
                "short": "レンジャーズ",
                "abbr": "TEX"
            },
            
            # ナショナルリーグ東地区
            "Atlanta Braves": {
                "full": "アトランタ・ブレーブス",
                "short": "ブレーブス",
                "abbr": "ATL"
            },
            "Miami Marlins": {
                "full": "マイアミ・マーリンズ",
                "short": "マーリンズ",
                "abbr": "MIA"
            },
            "New York Mets": {
                "full": "ニューヨーク・メッツ",
                "short": "メッツ",
                "abbr": "NYM"
            },
            "Philadelphia Phillies": {
                "full": "フィラデルフィア・フィリーズ",
                "short": "フィリーズ",
                "abbr": "PHI"
            },
            "Washington Nationals": {
                "full": "ワシントン・ナショナルズ",
                "short": "ナショナルズ",
                "abbr": "WSH"
            },
            
            # ナショナルリーグ中地区
            "Chicago Cubs": {
                "full": "シカゴ・カブス",
                "short": "カブス",
                "abbr": "CHC"
            },
            "Cincinnati Reds": {
                "full": "シンシナティ・レッズ",
                "short": "レッズ",
                "abbr": "CIN"
            },
            "Milwaukee Brewers": {
                "full": "ミルウォーキー・ブルワーズ",
                "short": "ブルワーズ",
                "abbr": "MIL"
            },
            "Pittsburgh Pirates": {
                "full": "ピッツバーグ・パイレーツ",
                "short": "パイレーツ",
                "abbr": "PIT"
            },
            "St. Louis Cardinals": {
                "full": "セントルイス・カージナルス",
                "short": "カージナルス",
                "abbr": "STL"
            },
            
            # ナショナルリーグ西地区
            "Arizona Diamondbacks": {
                "full": "アリゾナ・ダイヤモンドバックス",
                "short": "Dバックス",  # 一般的な略称
                "abbr": "ARI"
            },
            "Colorado Rockies": {
                "full": "コロラド・ロッキーズ",
                "short": "ロッキーズ",
                "abbr": "COL"
            },
            "Los Angeles Dodgers": {
                "full": "ロサンゼルス・ドジャース",
                "short": "ドジャース",
                "abbr": "LAD"
            },
            "San Diego Padres": {
                "full": "サンディエゴ・パドレス",
                "short": "パドレス",
                "abbr": "SD"
            },
            "San Francisco Giants": {
                "full": "サンフランシスコ・ジャイアンツ",
                "short": "ジャイアンツ",
                "abbr": "SF"
            }
        }
        
        # 選手名データベース（JSONファイルから読み込み）
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.player_names = json.load(f)
        else:
            # 初期データ（主要選手のみ）
            self.player_names = self._get_initial_player_data()
            self.save_database()
            
    def _get_initial_player_data(self):
        """初期選手データ（メディアで使用されている正確な表記）"""
        return {
            # 日本人選手（必ず正確に）
            "Shohei Ohtani": "大谷翔平",
            "Yoshinobu Yamamoto": "山本由伸",
            "Yu Darvish": "ダルビッシュ有",
            "Shota Imanaga": "今永昇太",
            "Masataka Yoshida": "吉田正尚",
            "Seiya Suzuki": "鈴木誠也",
            "Kodai Senga": "千賀滉大",
            "Yuki Matsui": "松井裕樹",
            
            # 2024-2025 主要選手（スポーツメディア準拠）
            "Aaron Judge": "アーロン・ジャッジ",
            "Mike Trout": "マイク・トラウト",
            "Mookie Betts": "ムーキー・ベッツ",
            "Ronald Acuña Jr.": "ロナルド・アクーニャJr.",
            "Juan Soto": "フアン・ソト",
            "Freddie Freeman": "フレディ・フリーマン",
            "José Altuve": "ホセ・アルトゥーベ",
            "Trea Turner": "トレア・ターナー",
            "Marcus Semien": "マーカス・セミエン",
            "Corey Seager": "コーリー・シーガー",
            "Bobby Witt Jr.": "ボビー・ウィットJr.",
            
            # エース投手
            "Gerrit Cole": "ゲリット・コール",
            "Spencer Strider": "スペンサー・ストライダー",
            "Zack Wheeler": "ザック・ウィーラー",
            "Corbin Burnes": "コービン・バーンズ",
            "Shane Bieber": "シェーン・ビーバー",
            "Jacob deGrom": "ジェイコブ・デグロム",
            "Max Scherzer": "マックス・シャーザー",
            "Justin Verlander": "ジャスティン・バーランダー",
            "Clayton Kershaw": "クレイトン・カーショー",
            
            # その他の有名選手
            "Vladimir Guerrero Jr.": "ブラディミール・ゲレーロJr.",
            "Fernando Tatis Jr.": "フェルナンド・タティスJr.",
            "Rafael Devers": "ラファエル・デバース",
            "Pete Alonso": "ピート・アロンソ",
            "Yordan Alvarez": "ヨルダン・アルバレス"
        }
        
    def save_database(self):
        """データベースを保存"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(self.player_names, f, ensure_ascii=False, indent=2)
            
    def get_team_name(self, team_name_en, format_type="short"):
        """
        チーム名を取得
        format_type: "full"（フル）, "short"（短縮）, "abbr"（略称）
        """
        team_data = self.TEAM_NAMES_OFFICIAL.get(team_name_en, {})
        return team_data.get(format_type, team_name_en)
        
    def get_player_name(self, player_name_en):
        """選手名を取得（なければ英語のまま）"""
        return self.player_names.get(player_name_en, player_name_en)
        
    def add_player_name(self, name_en, name_jp):
        """新しい選手名を追加"""
        self.player_names[name_en] = name_jp
        self.save_database()
        
    def update_from_csv(self, csv_path):
        """CSVファイルから一括更新（メディアから取得したデータ用）"""
        import csv
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['name_en'] and row['name_jp']:
                    self.player_names[row['name_en']] = row['name_jp']
        self.save_database()

# 使いやすい関数を提供
_db = None

def get_db():
    global _db
    if _db is None:
        _db = AccurateNameDatabase()
    return _db

def get_team_name_jp(team_name_en, format_type="short"):
    """チーム名を日本語で取得"""
    return get_db().get_team_name(team_name_en, format_type)

def get_player_name_jp(player_name_en):
    """選手名を日本語で取得"""
    return get_db().get_player_name(player_name_en)

# テスト
if __name__ == "__main__":
    db = AccurateNameDatabase()
    
    print("=== チーム名テスト ===")
    test_teams = ["New York Yankees", "Los Angeles Angels", "San Diego Padres"]
    for team in test_teams:
        print(f"{team}:")
        print(f"  フル: {db.get_team_name(team, 'full')}")
        print(f"  短縮: {db.get_team_name(team, 'short')}")
        print(f"  略称: {db.get_team_name(team, 'abbr')}")
        print()
        
    print("=== 選手名テスト ===")
    test_players = [
        "Shohei Ohtani",
        "Aaron Judge",
        "Mike Trout",
        "Unknown Player"  # データベースにない選手
    ]
    for player in test_players:
        print(f"{player} → {db.get_player_name(player)}")