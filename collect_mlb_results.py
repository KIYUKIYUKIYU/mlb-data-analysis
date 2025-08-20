import subprocess
import sys
import re
from datetime import datetime

def extract_game_info(text):
    """テキストから試合情報を抽出"""
    games = []
    
    # 試合情報のパターンを検索
    game_pattern = r'\*\*(.*?)\s+@\s+(.*?)\*\*\s+開始時刻:\s+(\d{2}/\d{2}\s+\d{2}:\d{2})'
    
    # テキストを分割して各試合を処理
    game_blocks = text.split('==================================================')
    
    for i in range(0, len(game_blocks)-1, 2):
        if i+1 < len(game_blocks):
            header = game_blocks[i]
            content = game_blocks[i+1]
            
            # ヘッダーから試合情報を抽出
            match = re.search(game_pattern, header)
            if match:
                away_team = match.group(1)
                home_team = match.group(2)
                start_time = match.group(3)
                
                # 完全な試合情報を構築
                game_info = f"**{away_team} @ {home_team}**\n"
                game_info += f"開始時刻: {start_time} (日本時間)\n"
                game_info += "=" * 50 + "\n"
                game_info += content.strip() + "\n"
                game_info += "=" * 50
                
                games.append(game_info)
    
    return games

def main():
    print("MLB 15試合結果を収集中...")
    print("=" * 80)
    
    # Discord環境変数を設定
    import os
    os.environ['DISCORD_WEBHOOK_URL'] = 'dummy'
    
    # 既存のスクリプトを実行して出力をキャプチャ
    try:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.discord_report_with_table"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5分のタイムアウト
        )
        
        output = result.stdout
        
        # 試合情報を抽出
        games = extract_game_info(output)
        
        # 結果を表示
        current_time = datetime.now().strftime("%H:%M")
        
        for i, game in enumerate(games, 1):
            print(f"\n{i}. {'_' * 50}")
            print("**新規**")
            print(f"**[{current_time}]**")
            print(game)
            print()
        
        print(f"\n収集完了: 全{len(games)}試合")
        
        # ファイルに保存
        with open('mlb_results_collected.txt', 'w', encoding='utf-8') as f:
            for i, game in enumerate(games, 1):
                f.write(f"{i}. {'_' * 50}\n")
                f.write("**新規**\n")
                f.write(f"**[{current_time}]**\n")
                f.write(game + "\n\n")
        
        print("\n結果は 'mlb_results_collected.txt' に保存されました。")
        
    except subprocess.TimeoutExpired:
        print("タイムアウト: 処理に時間がかかりすぎています。")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main()