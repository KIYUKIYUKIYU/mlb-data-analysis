#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
統合版MLBレポート生成システム
テキストレポートとHTMLレポートを同時生成
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 既存のモジュールをインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.mlb_complete_report_real import generate_complete_mlb_report
from scripts.report_visualizer import MLBReportVisualizer

def save_report_as_json(report_text, output_path):
    """
    テキストレポートをJSON形式で保存
    """
    # レポートを解析してJSON化（簡易版）
    report_data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "raw_text": report_text,
        "games": [],
        "team_stats": {},
        "player_stats": {
            "batters": [],
            "pitchers": []
        }
    }
    
    # テキストレポートから情報を抽出（実装例）
    lines = report_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        
        # セクション判定
        if '試合結果' in line or 'Game Results' in line:
            current_section = 'games'
        elif '打撃成績' in line or 'Batting Stats' in line:
            current_section = 'batting'
        elif '投手成績' in line or 'Pitching Stats' in line:
            current_section = 'pitching'
        
        # データ抽出（簡易版 - 実際のフォーマットに合わせて調整）
        if current_section == 'games' and ' vs ' in line:
            # 試合情報の抽出
            parts = line.split(' vs ')
            if len(parts) == 2:
                away_info = parts[0].strip()
                home_info = parts[1].strip()
                
                # スコア抽出（例: "Yankees 5" -> team="Yankees", score=5）
                game_info = {
                    "away_team": away_info.split()[0] if away_info else "",
                    "home_team": home_info.split()[0] if home_info else "",
                    "away_score": 0,
                    "home_score": 0,
                    "status": "Final"
                }
                report_data["games"].append(game_info)
    
    # JSON保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    return report_data

def integrate_mlb_reports():
    """
    統合版レポート生成
    1. テキストレポート生成
    2. JSONデータ保存
    3. HTMLレポート生成
    """
    print("=" * 60)
    print("⚾ MLB統合レポート生成システム")
    print("=" * 60)
    
    # 出力ディレクトリ作成
    os.makedirs("daily_reports", exist_ok=True)
    os.makedirs("daily_reports/html", exist_ok=True)
    os.makedirs("daily_reports/json", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y%m%d")
    
    # ステップ1: テキストレポート生成
    print("\n📝 テキストレポートを生成中...")
    text_report = generate_complete_mlb_report()
    
    # テキストレポート保存
    text_path = f"daily_reports/mlb_report_{timestamp}.txt"
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(text_report)
    print(f"✅ テキストレポート保存: {text_path}")
    
    # ステップ2: JSONデータ保存
    print("\n📊 JSONデータを生成中...")
    json_path = f"daily_reports/json/mlb_data_{date_str}.json"
    report_data = save_report_as_json(text_report, json_path)
    print(f"✅ JSONデータ保存: {json_path}")
    
    # ステップ3: HTMLレポート生成
    print("\n🎨 HTMLレポートを生成中...")
    visualizer = MLBReportVisualizer()
    visualizer.report_data = report_data
    html_path = f"daily_reports/html/mlb_report_{date_str}.html"
    visualizer.create_html_report(html_path)
    print(f"✅ HTMLレポート保存: {html_path}")
    
    # オプション: PDF生成
    try:
        print("\n📄 PDFレポートを生成中...")
        pdf_path = visualizer.create_pdf_report(html_path)
        if pdf_path:
            print(f"✅ PDFレポート保存: {pdf_path}")
    except Exception as e:
        print(f"⚠️ PDF生成はスキップされました: {e}")
    
    # 完了メッセージ
    print("\n" + "=" * 60)
    print("✨ 全レポートの生成が完了しました！")
    print("=" * 60)
    print(f"📁 テキスト: {text_path}")
    print(f"📁 JSON: {json_path}")
    print(f"📁 HTML: {html_path}")
    print("=" * 60)
    
    return {
        "text": text_path,
        "json": json_path,
        "html": html_path
    }

def cleanup_old_reports(days_to_keep=7):
    """
    古いレポートをクリーンアップ
    """
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    for folder in ["daily_reports", "daily_reports/html", "daily_reports/json"]:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        print(f"🗑️ 削除: {file_path}")

if __name__ == "__main__":
    try:
        # 古いレポートのクリーンアップ（オプション）
        # cleanup_old_reports(days_to_keep=30)
        
        # レポート生成
        integrate_mlb_reports()
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)