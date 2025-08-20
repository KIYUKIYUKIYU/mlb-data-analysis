 
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Team Name Converter - チーム名変換システム
英語のチーム名を日本語（カタカナ）に変換

実行: python -m scripts.team_name_converter
"""

# MLB全30チームの英語名とカタカナ名の対応辞書
MLB_TEAM_NAMES = {
    # アメリカンリーグ東地区
    "Baltimore Orioles": "ボルチモア・オリオールズ",
    "Boston Red Sox": "ボストン・レッドソックス",
    "New York Yankees": "ニューヨーク・ヤンキース",
    "Tampa Bay Rays": "タンパベイ・レイズ",
    "Toronto Blue Jays": "トロント・ブルージェイズ",
    
    # アメリカンリーグ中地区
    "Chicago White Sox": "シカゴ・ホワイトソックス",
    "Cleveland Guardians": "クリーブランド・ガーディアンズ",
    "Detroit Tigers": "デトロイト・タイガース",
    "Kansas City Royals": "カンザスシティ・ロイヤルズ",
    "Minnesota Twins": "ミネソタ・ツインズ",
    
    # アメリカンリーグ西地区
    "Houston Astros": "ヒューストン・アストロズ",
    "Los Angeles Angels": "ロサンゼルス・エンゼルス",
    "Oakland Athletics": "オークランド・アスレチックス",
    "Seattle Mariners": "シアトル・マリナーズ",
    "Texas Rangers": "テキサス・レンジャーズ",
    
    # ナショナルリーグ東地区
    "Atlanta Braves": "アトランタ・ブレーブス",
    "Miami Marlins": "マイアミ・マーリンズ",
    "New York Mets": "ニューヨーク・メッツ",
    "Philadelphia Phillies": "フィラデルフィア・フィリーズ",
    "Washington Nationals": "ワシントン・ナショナルズ",
    
    # ナショナルリーグ中地区
    "Chicago Cubs": "シカゴ・カブス",
    "Cincinnati Reds": "シンシナティ・レッズ",
    "Milwaukee Brewers": "ミルウォーキー・ブルワーズ",
    "Pittsburgh Pirates": "ピッツバーグ・パイレーツ",
    "St. Louis Cardinals": "セントルイス・カージナルス",
    
    # ナショナルリーグ西地区
    "Arizona Diamondbacks": "アリゾナ・ダイヤモンドバックス",
    "Colorado Rockies": "コロラド・ロッキーズ",
    "Los Angeles Dodgers": "ロサンゼルス・ドジャース",
    "San Diego Padres": "サンディエゴ・パドレス",
    "San Francisco Giants": "サンフランシスコ・ジャイアンツ"
}

# 略称版（スペース節約用）
MLB_TEAM_ABBREVIATIONS = {
    "Baltimore Orioles": "BAL",
    "Boston Red Sox": "BOS",
    "New York Yankees": "NYY",
    "Tampa Bay Rays": "TB",
    "Toronto Blue Jays": "TOR",
    "Chicago White Sox": "CWS",
    "Cleveland Guardians": "CLE",
    "Detroit Tigers": "DET",
    "Kansas City Royals": "KC",
    "Minnesota Twins": "MIN",
    "Houston Astros": "HOU",
    "Los Angeles Angels": "LAA",
    "Oakland Athletics": "OAK",
    "Seattle Mariners": "SEA",
    "Texas Rangers": "TEX",
    "Atlanta Braves": "ATL",
    "Miami Marlins": "MIA",
    "New York Mets": "NYM",
    "Philadelphia Phillies": "PHI",
    "Washington Nationals": "WSH",
    "Chicago Cubs": "CHC",
    "Cincinnati Reds": "CIN",
    "Milwaukee Brewers": "MIL",
    "Pittsburgh Pirates": "PIT",
    "St. Louis Cardinals": "STL",
    "Arizona Diamondbacks": "ARI",
    "Colorado Rockies": "COL",
    "Los Angeles Dodgers": "LAD",
    "San Diego Padres": "SD",
    "San Francisco Giants": "SF"
}

def get_team_name_jp(team_name_en):
    """英語のチーム名を日本語（カタカナ）に変換"""
    return MLB_TEAM_NAMES.get(team_name_en, team_name_en)

def get_team_abbreviation(team_name_en):
    """英語のチーム名を略称に変換"""
    return MLB_TEAM_ABBREVIATIONS.get(team_name_en, team_name_en[:3].upper())

# 選手名の一般的な変換ルール（主要選手のみ）
PLAYER_NAME_JP = {
    # 日本人選手
    "Shohei Ohtani": "大谷翔平",
    "Yoshinobu Yamamoto": "山本由伸",
    "Yu Darvish": "ダルビッシュ有",
    "Shota Imanaga": "今永昇太",
    "Masataka Yoshida": "吉田正尚",
    
    # スター選手（一部）
    "Aaron Judge": "アーロン・ジャッジ",
    "Mike Trout": "マイク・トラウト",
    "Mookie Betts": "ムーキー・ベッツ",
    "Ronald Acuña Jr.": "ロナルド・アクーニャJr.",
    "Juan Soto": "フアン・ソト",
    "Freddie Freeman": "フレディ・フリーマン",
    "Gerrit Cole": "ゲリット・コール",
    "Max Scherzer": "マックス・シャーザー",
    "Jacob deGrom": "ジェイコブ・デグロム",
    "Sandy Alcantara": "サンディ・アルカンタラ"
}

def get_player_name_jp(player_name_en):
    """選手名を日本語表記に変換（登録されている選手のみ）"""
    return PLAYER_NAME_JP.get(player_name_en, player_name_en)

# テスト用
if __name__ == "__main__":
    print("=== MLBチーム名変換テスト ===\n")
    
    # テスト用チーム
    test_teams = [
        "New York Yankees",
        "Los Angeles Angels",
        "Los Angeles Dodgers",
        "Chicago Cubs",
        "San Diego Padres"
    ]
    
    for team in test_teams:
        print(f"{team}")
        print(f"  日本語: {get_team_name_jp(team)}")
        print(f"  略称: {get_team_abbreviation(team)}")
        print()
    
    print("\n=== 選手名変換テスト ===\n")
    
    test_players = [
        "Shohei Ohtani",
        "Yoshinobu Yamamoto",
        "Aaron Judge",
        "Mike Trout",
        "Unknown Player"
    ]
    
    for player in test_players:
        print(f"{player} → {get_player_name_jp(player)}")