"""
日本式ハンデ Web入力システム（Discord Webhook版）
iPhoneのブラウザから入力して、既存のWebhookで配信
"""

from flask import Flask, render_template_string, request, jsonify
import json
import os
import re
import requests
from datetime import datetime
from typing import Dict, List, Optional
import socket

app = Flask(__name__)

# HTMLテンプレート（スマホ対応）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLB ハンデ入力システム</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            font-size: 24px;
        }
        textarea {
            width: 100%;
            height: 300px;
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 15px;
            margin-top: 10px;
            background-color: #5865F2;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
        }
        button:hover {
            background-color: #4752C4;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 15px;
            border-radius: 5px;
            display: none;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .preview {
            margin-top: 20px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
            display: none;
        }
        .loading {
            display: none;
            text-align: center;
            margin-top: 10px;
        }
        .ip-info {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚾ MLB ハンデ入力システム</h1>
        
        <p style="text-align: center; color: #666;">
            Signalからコピーしたハンデ情報を貼り付けてください
        </p>
        
        <textarea id="handicapInput" placeholder="例：
ヤンキース<1.8>
オリオールズ

レイズ<0.1>
タイガース"></textarea>
        
        <button onclick="parseHandicap()" id="parseBtn">解析する</button>
        <button onclick="sendToDiscord()" id="sendBtn" style="display:none;">Discordに送信</button>
        
        <div class="loading">
            <span>処理中...</span>
        </div>
        
        <div id="result" class="result"></div>
        <div id="preview" class="preview"></div>
        
        <div class="ip-info">
            アクセス可能なIP: <span id="serverIP"></span>
        </div>
    </div>
    
    <script>
        let parsedData = null;
        
        // サーバーIPを表示
        fetch('/api/server_info')
            .then(res => res.json())
            .then(data => {
                document.getElementById('serverIP').textContent = data.ip + ':' + data.port;
            });
        
        function parseHandicap() {
            const input = document.getElementById('handicapInput').value;
            if (!input.trim()) {
                showResult('テキストを入力してください', 'error');
                return;
            }
            
            document.getElementById('parseBtn').disabled = true;
            document.querySelector('.loading').style.display = 'block';
            
            fetch('/api/parse', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: input})
            })
            .then(res => res.json())
            .then(data => {
                document.querySelector('.loading').style.display = 'none';
                document.getElementById('parseBtn').disabled = false;
                
                if (data.success && data.games.length > 0) {
                    parsedData = data;
                    showResult(`✅ ${data.games.length}試合のハンデを検出しました`, 'success');
                    showPreview(data.games);
                    document.getElementById('sendBtn').style.display = 'block';
                } else {
                    showResult('❌ ハンデ情報が見つかりませんでした', 'error');
                }
            })
            .catch(err => {
                document.querySelector('.loading').style.display = 'none';
                document.getElementById('parseBtn').disabled = false;
                showResult('エラーが発生しました: ' + err, 'error');
            });
        }
        
        function sendToDiscord() {
            if (!parsedData) return;
            
            document.getElementById('sendBtn').disabled = true;
            document.querySelector('.loading').style.display = 'block';
            
            fetch('/api/send_discord', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(parsedData)
            })
            .then(res => res.json())
            .then(data => {
                document.querySelector('.loading').style.display = 'none';
                document.getElementById('sendBtn').disabled = false;
                
                if (data.success) {
                    showResult('✅ Discordに送信しました！', 'success');
                    document.getElementById('sendBtn').style.display = 'none';
                    document.getElementById('handicapInput').value = '';
                    document.getElementById('preview').style.display = 'none';
                } else {
                    showResult('❌ 送信エラー: ' + data.error, 'error');
                }
            });
        }
        
        function showResult(message, type) {
            const result = document.getElementById('result');
            result.textContent = message;
            result.className = 'result ' + type;
            result.style.display = 'block';
        }
        
        function showPreview(games) {
            const preview = document.getElementById('preview');
            let html = '<strong>検出したハンデ:</strong><br>';
            games.forEach((game, i) => {
                html += `${i+1}. ${game.favorite} -${game.handicap} vs ${game.underdog}<br>`;
            });
            preview.innerHTML = html;
            preview.style.display = 'block';
        }
    </script>
</body>
</html>
"""

class HandicapWebServer:
    """ハンデWeb処理クラス"""
    
    def __init__(self):
        self.data_dir = "handicap_data"
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
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
    
    def parse_handicap_text(self, text: str) -> List[Dict]:
        """ハンデテキストを解析（改良版）"""
        lines = text.strip().split('\n')
        games = []
        processed_teams = set()  # 処理済みチームを記録
        
        # まず、すべての有効な行を抽出
        valid_lines = []
        for line in lines:
            line = line.strip()
            # 不要な行をスキップ
            if (not line or re.match(r'\d+時', line) or 
                '[MLB]' in line or '[ＭＬＢ]' in line or '締切' in line or
                '---' in line):
                continue
            valid_lines.append(line)
        
        # 対戦カードを解析
        i = 0
        while i < len(valid_lines):
            line = valid_lines[i]
            
            # チーム名を取得（ハンデの有無に関わらず）
            handicap_match = re.match(r'(.+?)<(\d+\.?\d*)>$', line)
            
            if handicap_match:
                # ハンデ付きチーム
                team_with_handicap = handicap_match.group(1).strip()
                handicap_value = float(handicap_match.group(2))
            else:
                # ハンデなしチーム
                team_with_handicap = None
                handicap_value = None
            
            # 次の行を確認
            if i + 1 < len(valid_lines):
                next_line = valid_lines[i + 1]
                next_handicap_match = re.match(r'(.+?)<(\d+\.?\d*)>$', next_line)
                
                if handicap_match and not next_handicap_match:
                    # パターン1: ハンデ付き → ハンデなし
                    opponent = next_line.strip()
                    if team_with_handicap not in processed_teams and opponent not in processed_teams:
                        games.append({
                            "favorite": team_with_handicap,
                            "favorite_code": self.team_normalization.get(team_with_handicap, team_with_handicap),
                            "underdog": opponent,
                            "underdog_code": self.team_normalization.get(opponent, opponent),
                            "handicap": handicap_value
                        })
                        processed_teams.add(team_with_handicap)
                        processed_teams.add(opponent)
                        i += 2
                        continue
                
                elif not handicap_match and next_handicap_match:
                    # パターン2: ハンデなし → ハンデ付き
                    team_without_handicap = line.strip()
                    team_with_handicap_next = next_handicap_match.group(1).strip()
                    handicap_value_next = float(next_handicap_match.group(2))
                    
                    if team_without_handicap not in processed_teams and team_with_handicap_next not in processed_teams:
                        games.append({
                            "favorite": team_with_handicap_next,
                            "favorite_code": self.team_normalization.get(team_with_handicap_next, team_with_handicap_next),
                            "underdog": team_without_handicap,
                            "underdog_code": self.team_normalization.get(team_without_handicap, team_without_handicap),
                            "handicap": handicap_value_next
                        })
                        processed_teams.add(team_without_handicap)
                        processed_teams.add(team_with_handicap_next)
                        i += 2
                        continue
            
            i += 1
        
        return games
    
    def create_discord_message(self, games: List[Dict]) -> str:
        """Discord用メッセージを作成"""
        message = "**📊 MLBハンデ情報**\n"
        message += f"入力時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += "=" * 40 + "\n\n"
        
        for i, game in enumerate(games, 1):
            message += f"**{i}. {game['favorite']} (出し) vs {game['underdog']} (もらい)**\n"
            message += f"   ハンデ: **-{game['handicap']}**\n\n"
        
        return message

# インスタンス作成
handicap_server = HandicapWebServer()

@app.route('/')
def index():
    """メインページ"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/server_info')
def server_info():
    """サーバー情報を返す"""
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return jsonify({
        "hostname": hostname,
        "ip": ip,
        "port": 5000
    })

@app.route('/api/parse', methods=['POST'])
def parse_handicap():
    """ハンデテキストを解析"""
    try:
        data = request.json
        text = data.get('text', '')
        
        games = handicap_server.parse_handicap_text(text)
        
        return jsonify({
            "success": True,
            "games": games,
            "count": len(games)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/send_discord', methods=['POST'])
def send_to_discord():
    """Discordに送信"""
    try:
        data = request.json
        games = data.get('games', [])
        
        # Discord Webhook URL（環境変数から取得）
        webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if not webhook_url:
            return jsonify({
                "success": False,
                "error": "DISCORD_WEBHOOK_URLが設定されていません"
            })
        
        # メッセージ作成
        message = handicap_server.create_discord_message(games)
        
        # Discord送信
        response = requests.post(webhook_url, json={"content": message})
        
        if response.status_code == 204:
            # データ保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(handicap_server.data_dir, f"handicap_{timestamp}.json")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump({"games": games, "timestamp": timestamp}, f, ensure_ascii=False, indent=2)
            
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": f"Discord送信エラー: {response.status_code}"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    print("=" * 50)
    print("🌐 ハンデ入力Webサーバーを起動します")
    print("=" * 50)
    
    # IPアドレスを表示
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print(f"PC名: {hostname}")
    print(f"IPアドレス: {ip}")
    print(f"アクセスURL: http://{ip}:5000")
    print("=" * 50)
    print("iPhoneのブラウザから上記URLにアクセスしてください")
    print("※PCとiPhoneが同じWi-Fiに接続されている必要があります")
    print("Ctrl+Cで終了")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)