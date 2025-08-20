 
"""
日本式ハンデ 簡易入力システム
Signalからコピペしたテキストを即座にデータ化
"""

import re
import json
from datetime import datetime
import os
from typing import Dict, List, Optional

class HandicapInputSystem:
    """ハンデ入力・データ化システム"""
    
    def __init__(self, data_dir: str = "handicap_data"):
        """
        コンストラクタ
        
        Parameters:
        data_dir: str - データ保存先ディレクトリ
        """
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        # チーム名の正規化辞書
        self.team_normalization = {
            "ヤンキース": "NYY", "レッドソックス": "BOS", "オリオールズ": "BAL",
            "レンジャーズ": "TEX", "メッツ": "NYM", "ブレーブス": "ATL",
            "レッズ": "CIN", "ホワイトソックス": "CWS", "ダイヤモンドバックス": "ARI",
            "ブリュワーズ": "MIL", "パイレーツ": "PIT", "ツインズ": "MIN",
            "マリナーズ": "SEA", "カージナルス": "STL", "カブス": "CHC",
            "エンゼルス": "LAA", "パドレス": "SD", "ナショナルズ": "WSH",
            "ドジャース": "LAD", "ジャイアンツ": "SF", "アストロズ": "HOU",
            "タイガース": "DET", "ロイヤルズ": "KC", "フィリーズ": "PHI",
            "ガーディアンズ": "CLE", "レイズ": "TB", "ブルージェイズ": "TOR",
            "アスレチックス": "OAK", "マーリンズ": "MIA", "ロッキーズ": "COL"
        }
    
    def parse_input(self, text: str) -> Dict:
        """
        コピペされたテキストを解析
        時刻や締切情報は無視し、チームとハンデのみ抽出
        
        Parameters:
        text: str - 入力テキスト
        
        Returns:
        dict - 解析結果
        """
        lines = text.strip().split('\n')
        
        result = {
            "input_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "games": []
        }
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 空行、時刻、MLBタグなどは無視
            if (not line or 
                re.match(r'\d+時', line) or 
                '[MLB]' in line or '[ＭＬＢ]' in line or
                '締切' in line):
                i += 1
                continue
            
            # チーム名とハンデの検出
            handicap_match = re.match(r'(.+?)<(\d+\.?\d*)>$', line)
            
            if handicap_match:
                # ハンデ付きチーム（フェイバリット）
                team_name = handicap_match.group(1).strip()
                handicap_value = float(handicap_match.group(2))
                
                # 次の行を対戦相手として取得
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    
                    # 次の行もハンデ持ちかチェック
                    next_handicap = re.match(r'(.+?)<(\d+\.?\d*)>$', next_line)
                    if next_handicap:
                        # エラー：両方にハンデがある
                        print(f"⚠️ 警告: 両チームにハンデあり - {team_name} vs {next_handicap.group(1)}")
                        opponent_name = next_handicap.group(1).strip()
                    else:
                        opponent_name = next_line
                    
                    # 有効な対戦カードなら追加
                    if opponent_name and not re.match(r'\d+時', opponent_name) and '[' not in opponent_name:
                        game_data = self._create_game_data(team_name, opponent_name, handicap_value)
                        result["games"].append(game_data)
                        i += 2
                        continue
            else:
                # ハンデなしのチーム名
                # 前の行がペアでない場合のみ処理
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    if (prev_line and 
                        not re.match(r'.+<\d+\.?\d*>$', prev_line) and
                        not re.match(r'\d+時', prev_line) and
                        '[' not in prev_line and
                        '締切' not in prev_line):
                        # ハンデなしの対戦カード
                        game_data = self._create_game_data(prev_line, line, 0.0)
                        result["games"].append(game_data)
            
            i += 1
        
        return result
    
    def _create_game_data(self, favorite: str, underdog: str, handicap: float) -> Dict:
        """
        試合データを作成
        
        Parameters:
        favorite: str - フェイバリットチーム名
        underdog: str - アンダードッグチーム名
        handicap: float - ハンデ値
        
        Returns:
        dict - 試合データ
        """
        return {
            "favorite": {
                "name": favorite,
                "code": self.team_normalization.get(favorite, favorite),
                "handicap": handicap
            },
            "underdog": {
                "name": underdog,
                "code": self.team_normalization.get(underdog, underdog)
            },
            "handicap_type": self._determine_handicap_type(handicap)
        }
    
    def _determine_handicap_type(self, handicap: float) -> str:
        """ハンデタイプを判定"""
        if handicap == 0:
            return "even"
        elif handicap % 0.5 == 0 and handicap % 1.0 != 0:
            return "half"
        else:
            return "decimal"
    
    def save_data(self, parsed_data: Dict) -> str:
        """
        データを保存
        
        Returns:
        str - 保存先ファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.data_dir, f"handicap_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_data, f, ensure_ascii=False, indent=2)
        
        return filename
    
    def display_summary(self, parsed_data: Dict) -> str:
        """
        解析結果のサマリーを表示
        
        Returns:
        str - サマリーテキスト
        """
        output = []
        output.append("=" * 50)
        output.append("📊 ハンデ情報を解析しました")
        output.append(f"入力時刻: {parsed_data['input_time']}")
        output.append(f"試合数: {len(parsed_data['games'])}")
        output.append("=" * 50)
        
        for i, game in enumerate(parsed_data['games'], 1):
            fav = game['favorite']
            und = game['underdog']
            
            if fav['handicap'] > 0:
                output.append(f"{i}. {fav['name']}({fav['code']}) -{fav['handicap']} vs {und['name']}({und['code']})")
            else:
                output.append(f"{i}. {fav['name']}({fav['code']}) vs {und['name']}({und['code']}) [EVEN]")
        
        return "\n".join(output)


def main():
    """メイン実行関数"""
    system = HandicapInputSystem()
    
    print("=" * 50)
    print("🎯 日本式ハンデ入力システム")
    print("=" * 50)
    print("Signalからコピーしたテキストを貼り付けてください。")
    print("入力が終わったら、空行を入力してEnterを押してください。")
    print("-" * 50)
    
    # 複数行の入力を受け付ける
    lines = []
    while True:
        try:
            line = input()
            if line == "":
                if lines:  # 既に入力がある場合は終了
                    break
            lines.append(line)
        except EOFError:
            break
    
    if not lines:
        print("入力がありませんでした。")
        return
    
    # テキストを結合
    input_text = "\n".join(lines)
    
    # 解析実行
    try:
        parsed_data = system.parse_input(input_text)
        
        # 結果表示
        print("\n" + system.display_summary(parsed_data))
        
        # データ保存
        if parsed_data['games']:
            filename = system.save_data(parsed_data)
            print(f"\n💾 データを保存しました: {filename}")
            
            # 既存のMLBシステムとの連携用にも保存
            latest_file = os.path.join(system.data_dir, "latest_handicap.json")
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, f, ensure_ascii=False, indent=2)
            print(f"📌 最新データ: {latest_file}")
        else:
            print("\n⚠️ 有効な試合データが見つかりませんでした。")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    # スタンドアロンで実行
    main()
    
    # バッチ処理用の関数も提供
    def process_text(text: str) -> Dict:
        """外部から呼び出し可能な処理関数"""
        system = HandicapInputSystem()
        return system.parse_input(text)