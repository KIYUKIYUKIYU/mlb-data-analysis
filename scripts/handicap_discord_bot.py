"""
日本式ハンデ Discord Bot
DMでハンデ情報を受信して、MLBレポートと統合
"""

import discord
from discord.ext import commands
import json
import os
import re
from datetime import datetime
import asyncio
from typing import Dict, List, Optional

# Bot設定
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

class HandicapBot:
    """ハンデ処理用のBotクラス"""
    
    def __init__(self):
        self.data_dir = "handicap_data"
        self.reports_dir = "reports"
        
        # ディレクトリ作成
        for dir_path in [self.data_dir, self.reports_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        
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
        
        # 英語名からコードへの変換も追加
        self.team_code_mapping = {
            "Pirates": "PIT", "Brewers": "MIL", "Yankees": "NYY", 
            "Orioles": "BAL", "Rays": "TB", "Tigers": "DET",
            "Rangers": "TEX", "Blue Jays": "TOR", "White Sox": "CWS",
            "Marlins": "MIA", "Braves": "ATL", "Twins": "MIN",
            "Cardinals": "STL", "Reds": "CIN", "Cubs": "CHC",
            "Mariners": "SEA", "Rockies": "COL", "Diamondbacks": "ARI",
            "Athletics": "OAK", "Guardians": "CLE", "Giants": "SF",
            "Red Sox": "BOS", "Angels": "LAA", "Astros": "HOU",
            "Padres": "SD", "Royals": "KC", "Dodgers": "LAD",
            "Nationals": "WSH", "Phillies": "PHI", "Mets": "NYM"
        }
    
    def parse_handicap_text(self, text: str) -> List[Dict]:
        """ハンデテキストを解析"""
        lines = text.strip().split('\n')
        games = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 不要な行をスキップ
            if (not line or re.match(r'\d+時', line) or 
                '[MLB]' in line or '[ＭＬＢ]' in line or '締切' in line):
                i += 1
                continue
            
            # ハンデ付きチームの検出
            handicap_match = re.match(r'(.+?)<(\d+\.?\d*)>$', line)
            if handicap_match:
                team_name = handicap_match.group(1).strip()
                handicap_value = float(handicap_match.group(2))
                
                # 次の行が対戦相手
                if i + 1 < len(lines):
                    opponent = lines[i + 1].strip()
                    if opponent and not re.match(r'.+<\d+\.?\d*>$', opponent):
                        games.append({
                            "favorite": team_name,
                            "favorite_code": self.team_normalization.get(team_name, team_name),
                            "underdog": opponent,
                            "underdog_code": self.team_normalization.get(opponent, opponent),
                            "handicap": handicap_value
                        })
                        i += 2
                        continue
            
            i += 1
        
        return games
    
    async def load_today_mlb_data(self) -> Dict:
        """今日のMLBレポートデータを読み込み"""
        # 最新のMLBレポートを探す
        today = datetime.now().strftime("%Y%m%d")
        report_file = os.path.join(self.reports_dir, f"mlb_report_{today}.json")
        
        if os.path.exists(report_file):
            with open(report_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # デバッグ用のサンプルデータ
        return {
            "games": [
                {
                    "away_team": "Pittsburgh Pirates",
                    "home_team": "Milwaukee Brewers",
                    "game_time": "06/24 08:40"
                }
            ]
        }
    
    def match_handicap_to_game(self, handicap_data: Dict, mlb_game: Dict) -> Optional[Dict]:
        """ハンデデータとMLB試合データをマッチング"""
        # チーム名でマッチング試行
        away_team = mlb_game.get("away_team", "")
        home_team = mlb_game.get("home_team", "")
        
        # コードで比較
        away_code = self.team_code_mapping.get(away_team, "")
        home_code = self.team_code_mapping.get(home_team, "")
        
        if ((handicap_data["favorite_code"] == away_code and 
             handicap_data["underdog_code"] == home_code) or
            (handicap_data["favorite_code"] == home_code and 
             handicap_data["underdog_code"] == away_code)):
            return {
                "game": mlb_game,
                "handicap": handicap_data
            }
        
        return None
    
    async def create_integrated_report(self, handicap_games: List[Dict]) -> str:
        """統合レポートを作成"""
        mlb_data = await self.load_today_mlb_data()
        matched_games = []
        unmatched_handicaps = []
        
        # マッチング処理
        for h_game in handicap_games:
            matched = False
            for mlb_game in mlb_data.get("games", []):
                if self.match_handicap_to_game(h_game, mlb_game):
                    matched_games.append({
                        "mlb": mlb_game,
                        "handicap": h_game
                    })
                    matched = True
                    break
            
            if not matched:
                unmatched_handicaps.append(h_game)
        
        # レポート作成
        report = "📊 **MLBハンデ統合レポート**\n"
        report += f"更新時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "=" * 50 + "\n\n"
        
        if matched_games:
            report += "**✅ マッチング成功した試合:**\n"
            for match in matched_games:
                mlb = match["mlb"]
                h = match["handicap"]
                report += f"\n**{mlb['away_team']} @ {mlb['home_team']}**\n"
                report += f"開始時刻: {mlb['game_time']} (日本時間)\n"
                report += f"**ハンデ: {h['favorite']} -{h['handicap']}**\n"
                report += "-" * 30 + "\n"
        
        if unmatched_handicaps:
            report += "\n**⚠️ マッチングできなかったハンデ:**\n"
            for h in unmatched_handicaps:
                report += f"- {h['favorite']} -{h['handicap']} vs {h['underdog']}\n"
        
        return report

# Botインスタンス
handicap_bot = HandicapBot()

@bot.event
async def on_ready():
    """Bot起動時の処理"""
    print(f'{bot.user} として起動しました！')
    print(f'Bot ID: {bot.user.id}')
    print('DMでハンデ情報を送信してください。')

@bot.event
async def on_message(message):
    """メッセージ受信時の処理"""
    # Bot自身のメッセージは無視
    if message.author == bot.user:
        return
    
    # DMチャンネルでのメッセージのみ処理
    if isinstance(message.channel, discord.DMChannel):
        print(f"DMを受信: {message.author.name}")
        
        # ハンデっぽいテキストかチェック
        if '<' in message.content and '>' in message.content:
            await message.add_reaction('👀')  # 処理開始を示す
            
            try:
                # ハンデ解析
                games = handicap_bot.parse_handicap_text(message.content)
                
                if games:
                    # 解析成功
                    await message.add_reaction('✅')
                    
                    # 結果を返信
                    result_msg = f"**解析結果: {len(games)}試合のハンデを検出**\n"
                    for i, game in enumerate(games, 1):
                        result_msg += f"{i}. {game['favorite']} -{game['handicap']} vs {game['underdog']}\n"
                    
                    await message.channel.send(result_msg)
                    
                    # 統合レポート作成
                    await message.channel.send("📝 統合レポートを作成中...")
                    report = await handicap_bot.create_integrated_report(games)
                    
                    # レポートを分割送信（Discordの文字数制限対策）
                    if len(report) > 2000:
                        chunks = [report[i:i+1900] for i in range(0, len(report), 1900)]
                        for chunk in chunks:
                            await message.channel.send(chunk)
                    else:
                        await message.channel.send(report)
                    
                    # データ保存
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_path = os.path.join(handicap_bot.data_dir, f"handicap_{timestamp}.json")
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump({"games": games, "timestamp": timestamp}, f, ensure_ascii=False, indent=2)
                    
                    await message.channel.send(f"💾 データを保存しました: `{save_path}`")
                else:
                    await message.add_reaction('❌')
                    await message.channel.send("⚠️ ハンデ情報が見つかりませんでした。")
            
            except Exception as e:
                await message.add_reaction('💥')
                await message.channel.send(f"❌ エラーが発生しました: {str(e)}")
                print(f"エラー詳細: {e}")
        else:
            # ハンデ以外のメッセージ
            await message.channel.send(
                "ハンデ情報を送信してください。\n"
                "例:\n```\n"
                "ヤンキース<1.8>\n"
                "オリオールズ\n"
                "```"
            )

# Botトークンを環境変数から取得
if __name__ == "__main__":
    token = os.environ.get('DISCORD_BOT_TOKEN')
    if not token:
        print("エラー: DISCORD_BOT_TOKENが設定されていません。")
        print("set DISCORD_BOT_TOKEN=your_bot_token_here")
    else:
        bot.run(token)