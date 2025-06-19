"""
MLB予想レポート生成＆Discord配信システム
HTMLレポートを作成し、Discord Webhookで配信
"""
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from discord_webhook import DiscordWebhook, DiscordEmbed
from scripts.daily_prediction import DailyPredictionSystem
from scripts.visualize_matchup import MatchupVisualizer


class ReportPublisher:
    def __init__(self, discord_webhook_url: str = None):
        self.predictor = DailyPredictionSystem()
        self.visualizer = MatchupVisualizer()
        self.webhook_url = discord_webhook_url
        self.reports_path = "data/reports"
        
        # レポート用フォルダ作成
        if not os.path.exists(self.reports_path):
            os.makedirs(self.reports_path)
            
    def generate_html_report(self, predictions: List[Dict], date_str: str) -> str:
        """HTML形式のレポートを生成"""
        html_content = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB予想レポート - {date_str}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #003087;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .game-card {{
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .prediction {{
            font-size: 1.2em;
            font-weight: bold;
            color: #003087;
            margin: 10px 0;
        }}
        .confidence-high {{ color: #28a745; }}
        .confidence-medium {{ color: #ffc107; }}
        .confidence-low {{ color: #dc3545; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 20px;
        }}
        .team-stats {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚾ MLB予想レポート</h1>
        <h2>{date_str}</h2>
        <p>AIによる試合予想と分析</p>
    </div>
"""
        
        # 各試合の詳細
        for pred in predictions:
            confidence_class = 'high' if pred['confidence'] >= 3 else 'medium' if pred['confidence'] >= 2 else 'low'
            confidence_text = '高' if pred['confidence'] >= 3 else '中' if pred['confidence'] >= 2 else '低'
            
            winner = pred['away_team'] if pred['prediction'] == 'away' else pred['home_team']
            
            html_content += f"""
    <div class="game-card">
        <h3>🏟️ {pred['away_team']} @ {pred['home_team']}</h3>
        <p><strong>先発投手:</strong> {pred['away_starter']} vs {pred['home_starter']}</p>
        
        <div class="prediction">
            予想勝者: {winner} 
            <span class="confidence-{confidence_class}">（信頼度: {confidence_text}）</span>
        </div>
        
        <div class="stats-grid">
            <div class="team-stats">
                <h4>{pred['away_team']}</h4>
                <p>総合ポイント: {pred['away_points']}</p>
            </div>
            <div class="team-stats">
                <h4>{pred['home_team']}</h4>
                <p>総合ポイント: {pred['home_points']}</p>
            </div>
        </div>
    </div>
"""
        
        # フッター
        html_content += f"""
    <div class="footer">
        <p>Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>MLB Data Analysis System v1.0</p>
    </div>
</body>
</html>
"""
        
        # HTMLファイル保存
        html_path = os.path.join(self.reports_path, f"report_{date_str.replace('/', '-')}.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"📄 HTMLレポート生成: {html_path}")
        return html_path
        
    def send_to_discord(self, predictions: List[Dict], date_str: str, graph_paths: List[str] = None):
        """Discord Webhookで結果を配信"""
        if not self.webhook_url:
            print("⚠️  Discord Webhook URLが設定されていません")
            return
            
        webhook = DiscordWebhook(url=self.webhook_url)
        
        # メイン埋め込み
        embed = DiscordEmbed(
            title=f"⚾ MLB予想レポート - {date_str}",
            description=f"明日の試合予想（{len(predictions)}試合）",
            color='03b2f8'
        )
        
        # タイムスタンプ
        embed.set_timestamp()
        
        # 各試合の予想を追加
        for pred in predictions[:5]:  # 最初の5試合のみ（Discordの制限）
            winner = pred['away_team'] if pred['prediction'] == 'away' else pred['home_team']
            confidence = '🟢' if pred['confidence'] >= 3 else '🟡' if pred['confidence'] >= 2 else '🔴'
            
            embed.add_embed_field(
                name=f"{pred['away_team']} @ {pred['home_team']}",
                value=f"予想: **{winner}** {confidence}\n先発: {pred['away_starter']} vs {pred['home_starter']}",
                inline=False
            )
            
        # 統計情報
        home_wins = sum(1 for p in predictions if p['prediction'] == 'home')
        away_wins = sum(1 for p in predictions if p['prediction'] == 'away')
        high_confidence = sum(1 for p in predictions if p['confidence'] >= 3)
        
        embed.add_embed_field(
            name="📊 予想統計",
            value=f"ホーム勝利: {home_wins}\nアウェイ勝利: {away_wins}\n高信頼度: {high_confidence}",
            inline=True
        )
        
        webhook.add_embed(embed)
        
        # グラフがある場合は添付
        if graph_paths:
            for path in graph_paths[:3]:  # 最初の3つまで
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        webhook.add_file(file=f.read(), filename=os.path.basename(path))
                        
        # 送信
        response = webhook.execute()
        
        if response.status_code == 200:
            print("✅ Discord配信成功！")
        else:
            print(f"❌ Discord配信失敗: {response.status_code}")
            
    def create_summary_graph(self, predictions: List[Dict]) -> str:
        """予想サマリーのグラフを作成"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # グラフ1: 予想の内訳
        home_wins = sum(1 for p in predictions if p['prediction'] == 'home')
        away_wins = sum(1 for p in predictions if p['prediction'] == 'away')
        
        ax1.pie([home_wins, away_wins], labels=['ホーム', 'アウェイ'], 
                autopct='%1.1f%%', startangle=90, colors=['#003087', '#BD3039'])
        ax1.set_title('予想勝者の内訳')
        
        # グラフ2: 信頼度分布
        high = sum(1 for p in predictions if p['confidence'] >= 3)
        medium = sum(1 for p in predictions if p['confidence'] >= 2 and p['confidence'] < 3)
        low = sum(1 for p in predictions if p['confidence'] < 2)
        
        ax2.bar(['高', '中', '低'], [high, medium, low], 
                color=['#28a745', '#ffc107', '#dc3545'])
        ax2.set_title('予想信頼度の分布')
        ax2.set_ylabel('試合数')
        
        plt.tight_layout()
        
        # 保存
        graph_path = os.path.join(self.reports_path, f"summary_{datetime.now().strftime('%Y%m%d')}.png")
        plt.savefig(graph_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return graph_path
        
    def publish_daily_report(self):
        """日次レポートを生成・配信"""
        print("\n" + "="*60)
        print("📨 日次予想レポート配信システム")
        print("="*60)
        
        # 予想を生成
        games = self.predictor.get_tomorrow_games_mlb_time()
        
        if not games:
            print("明日は試合がありません。")
            return
            
        predictions = []
        
        # 各試合を分析（デモのため最初の3試合）
        print(f"\n明日の試合数: {len(games)} (デモ: 3試合分析)")
        
        for i, game in enumerate(games[:3], 1):
            print(f"\n[{i}/3] 分析中...", end="")
            prediction = self.predictor.analyze_matchup_for_prediction(game)
            predictions.append(prediction)
            
        # 日付
        japan_tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y/%m/%d')
        
        # HTMLレポート生成
        html_path = self.generate_html_report(predictions, japan_tomorrow)
        
        # サマリーグラフ作成
        summary_graph = self.create_summary_graph(predictions)
        
        # Discord配信
        self.send_to_discord(predictions, japan_tomorrow, [summary_graph])
        
        print(f"\n✅ レポート配信完了！")
        print(f"📁 HTMLレポート: {html_path}")
        

def main():
    """メイン実行関数"""
    # Discord Webhook URLを設定（環境変数または直接指定）
    webhook_url = os.getenv('DISCORD_WEBHOOK_URL', None)
    
    if not webhook_url:
        print("\n⚠️  Discord Webhook URLを設定してください")
        print("設定方法:")
        print("1. DiscordでWebhook URLを取得")
        print("2. 環境変数 DISCORD_WEBHOOK_URL に設定")
        print("3. または、このスクリプトの webhook_url 変数に直接記入")
        print("\n今回はHTMLレポートのみ生成します。")
        
    publisher = ReportPublisher(webhook_url)
    publisher.publish_daily_report()
    

if __name__ == "__main__":
    main()