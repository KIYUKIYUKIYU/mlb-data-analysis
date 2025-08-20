#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MLB試合レポートPDF生成システム
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import pytz
from pathlib import Path
import json
from jinja2 import Template
import pdfkit  # wkhtmltopdfが必要
from scripts.discord_report_with_table import DiscordReportWithTable

class MLBPDFReporter(DiscordReportWithTable):
    def __init__(self):
        super().__init__()
        self.template_path = Path("templates/mlb_matchup_template.html")
        self.output_dir = Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_match_html(self, game_data):
        """1試合のHTMLを生成"""
        # テンプレート読み込み
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template_str = f.read()
        
        # データを準備
        template_data = {
            'date': datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y.%m.%d'),
            'time': game_data.get('game_time', '未定'),
            'away_team': game_data['away_team'],
            'home_team': game_data['home_team'],
            'away_pitcher': game_data.get('away_pitcher', {}).get('name', '未定'),
            'home_pitcher': game_data.get('home_pitcher', {}).get('name', '未定'),
            'away_pitcher_stats': game_data.get('away_pitcher', {}),
            'home_pitcher_stats': game_data.get('home_pitcher', {}),
            'away_bullpen': game_data.get('away_bullpen', {}),
            'home_bullpen': game_data.get('home_bullpen', {}),
            'away_batting': game_data.get('away_team_batting', {}),
            'home_batting': game_data.get('home_team_batting', {})
        }
        
        # HTMLを生成
        template = Template(template_str)
        html = template.render(**template_data)
        
        return html
    
    def generate_all_reports(self):
        """全試合のPDFレポートを生成"""
        # 明日の試合データを取得
        jst = pytz.timezone('Asia/Tokyo')
        now_jst = datetime.now(jst)
        tomorrow_est = (now_jst - timedelta(hours=13)).date()
        
        print(f"PDFレポート生成開始: {tomorrow_est}")
        
        # APIから試合データ取得
        response = self.client._make_request(
            f"schedule?sportId=1&date={tomorrow_est}&hydrate=probablePitcher,team"
        )
        
        if not response or 'dates' not in response:
            print("試合データが取得できません")
            return
            
        games = response['dates'][0]['games'] if response['dates'] else []
        print(f"{len(games)}試合のレポートを生成します...")
        
        # 各試合のデータを処理
        for i, game in enumerate(games):
            print(f"試合 {i+1}/{len(games)}: 処理中...")
            
            # 試合データを収集（既存のメソッドを活用）
            game_data = self.process_game_data(game)
            
            # HTMLを生成
            html = self.generate_match_html(game_data)
            
            # PDFに変換
            output_filename = f"{tomorrow_est}_{game['teams']['away']['team']['abbreviation']}_vs_{game['teams']['home']['team']['abbreviation']}.pdf"
            output_path = self.output_dir / output_filename
            
            try:
                pdfkit.from_string(html, str(output_path))
                print(f"  ✓ PDF生成完了: {output_filename}")
            except Exception as e:
                print(f"  ✗ PDF生成エラー: {e}")
    
    def process_game_data(self, game):
        """既存のデータ処理を再利用"""
        # 基本データ
        game_data = {
            'game_id': game['gamePk'],
            'away_team': game['teams']['away']['team']['name'],
            'home_team': game['teams']['home']['team']['name'],
            'away_team_id': game['teams']['away']['team']['id'],
            'home_team_id': game['teams']['home']['team']['id'],
        }
        
        # 先発投手データ
        if 'probablePitcher' in game['teams']['away']:
            pitcher_id = game['teams']['away']['probablePitcher']['id']
            pitcher_name = game['teams']['away']['probablePitcher']['fullName']
            game_data['away_pitcher'] = self.get_complete_pitcher_stats(pitcher_id, pitcher_name, 2025)
        
        if 'probablePitcher' in game['teams']['home']:
            pitcher_id = game['teams']['home']['probablePitcher']['id']
            pitcher_name = game['teams']['home']['probablePitcher']['fullName']
            game_data['home_pitcher'] = self.get_complete_pitcher_stats(pitcher_id, pitcher_name, 2025)
        
        # チーム打撃統計
        game_data['away_team_batting'] = self.get_team_batting_stats(game_data['away_team_id'], 2025)
        game_data['home_team_batting'] = self.get_team_batting_stats(game_data['home_team_id'], 2025)
        
        # 中継ぎ陣統計
        game_data['away_bullpen'] = self.get_team_bullpen_stats(game_data['away_team_id'], 2025)
        game_data['home_bullpen'] = self.get_team_bullpen_stats(game_data['home_team_id'], 2025)
        
        return game_data

if __name__ == "__main__":
    # 必要なパッケージ確認
    try:
        import pdfkit
        import jinja2
    except ImportError:
        print("必要なパッケージをインストールしてください:")
        print("pip install pdfkit jinja2")
        sys.exit(1)
    
    # wkhtmltopdfの確認
    try:
        pdfkit.configuration()
    except:
        print("wkhtmltopdfをインストールしてください:")
        print("https://wkhtmltopdf.org/downloads.html")
        sys.exit(1)
    
    # レポート生成
    reporter = MLBPDFReporter()
    reporter.generate_all_reports()