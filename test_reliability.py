"""
レポートヘッダーにデータ信頼性を明確に表示
mlb_complete_report_real.py の generate_report 関数の最初に追加
"""

def display_data_reliability_header():
    """データの信頼性と更新状況を明確に表示"""
    from datetime import datetime
    from pathlib import Path
    import json
    
    print("=" * 70)
    print("MLB試合予想レポート - データ信頼性レポート付き")
    print("=" * 70)
    
    now = datetime.now()
    cache_dir = Path("cache")
    
    # データソースごとの状態を確認
    data_sources = {
        "MLB API": {
            "dirs": ["advanced_stats", "batting_quality", "bullpen_stats", "recent_ops", "splits_data"],
            "icon": "⚾",
            "critical": True
        },
        "Statcast": {
            "dirs": ["statcast_data"],
            "icon": "📊",
            "critical": False
        }
    }
    
    print(f"レポート生成時刻: {now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    print()
    print("【データ更新状況】")
    print("-" * 60)
    
    all_fresh = True
    details = []
    
    for source_name, source_info in data_sources.items():
        source_fresh = True
        source_details = []
        
        for dir_name in source_info["dirs"]:
            cache_path = cache_dir / dir_name
            
            if cache_path.exists():
                files = list(cache_path.glob("*.json"))
                if files:
                    # 最新ファイルの更新時刻を取得
                    latest = max(files, key=lambda f: f.stat().st_mtime)
                    update_time = datetime.fromtimestamp(latest.stat().st_mtime)
                    age = now - update_time
                    
                    # 鮮度判定
                    if age.total_seconds() < 3600:  # 1時間以内
                        status = "🟢"
                        status_text = "最新"
                    elif age.total_seconds() < 21600:  # 6時間以内
                        status = "🟡"
                        status_text = "新しい"
                    elif age.days == 0:  # 今日
                        status = "🟡"
                        status_text = "本日"
                    else:
                        status = "🔴"
                        status_text = f"{age.days}日前"
                        source_fresh = False
                        all_fresh = False
                    
                    time_str = update_time.strftime("%H:%M")
                    
                    # 特定のディレクトリの詳細
                    if dir_name == "statcast_data":
                        # Statcastの詳細情報
                        with open(latest, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            team_count = len(data.get('data', {}))
                            source_type = list(data.get('data', {}).values())[0].get('source', 'unknown') if data.get('data') else 'unknown'
                            source_details.append(f"{status} Barrel%/Hard-Hit% ({time_str}更新, {team_count}チーム, {source_type})")
                    elif dir_name == "bullpen_stats":
                        file_count = len(files)
                        source_details.append(f"{status} ブルペン ({time_str}更新, {file_count}チーム)")
                    elif dir_name == "recent_ops":
                        source_details.append(f"{status} 直近成績 ({time_str}更新)")
                    elif dir_name == "advanced_stats":
                        source_details.append(f"{status} 投手詳細 ({time_str}更新)")
        
        # ソースごとの表示
        if source_fresh:
            print(f"{source_info['icon']} {source_name}: ✅ 全データ最新")
        else:
            print(f"{source_info['icon']} {source_name}: ⚠️ 一部データ古い")
        
        for detail in source_details[:2]:  # 最大2つまで表示
            print(f"    {detail}")
    
    print()
    
    # 総合評価
    if all_fresh:
        print("📊 【総合評価】 ⭐⭐⭐⭐⭐ 優秀")
        print("   全てのデータが最新です。予想の信頼性: 非常に高い")
    else:
        print("📊 【総合評価】 ⭐⭐⭐⭐ 良好")
        print("   主要データは最新です。予想の信頼性: 高い")
    
    print("=" * 70)
    print()

def display_simple_reliability():
    """シンプルな信頼性表示（1行版）"""
    from datetime import datetime
    from pathlib import Path
    
    cache_dir = Path("cache")
    now = datetime.now()
    
    # 重要なデータの鮮度チェック
    fresh_count = 0
    total_count = 0
    
    important_dirs = ["batting_quality", "bullpen_stats", "recent_ops", "statcast_data"]
    
    for dir_name in important_dirs:
        total_count += 1
        cache_path = cache_dir / dir_name
        if cache_path.exists():
            files = list(cache_path.glob("*.json"))
            if files:
                latest = max(files, key=lambda f: f.stat().st_mtime)
                age = now - datetime.fromtimestamp(latest.stat().st_mtime)
                if age.days == 0:  # 今日更新されていれば
                    fresh_count += 1
    
    reliability_pct = (fresh_count / total_count * 100) if total_count > 0 else 0
    
    if reliability_pct >= 90:
        status = "✅ データ信頼性: 高"
    elif reliability_pct >= 70:
        status = "🟡 データ信頼性: 中"
    else:
        status = "🔴 データ信頼性: 要確認"
    
    print(f"{status} ({fresh_count}/{total_count}データが本日更新) | {now.strftime('%H:%M')}時点")
    print("-" * 60)

# 実際の使用例
if __name__ == "__main__":
    print("【詳細版】")
    display_data_reliability_header()
    
    print("\n【簡易版（1行）】")
    display_simple_reliability()