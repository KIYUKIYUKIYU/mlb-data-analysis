"""
MLBデータ分析システム - データ更新状況チェッカー
各モジュールがどのAPIを使い、いつ更新されたかを確認
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def check_cache_status():
    """キャッシュファイルの更新状況を確認"""
    
    cache_dir = Path("cache")
    results = {
        "summary": {},
        "details": {}
    }
    
    # 各キャッシュディレクトリをチェック
    cache_types = {
        "advanced_stats": "投手詳細統計（ERA, FIP, xFIP等）",
        "batting_quality": "打撃品質統計（wOBA, Barrel%等）", 
        "bullpen_stats": "ブルペン統計（中継ぎ陣）",
        "recent_ops": "直近試合OPS",
        "splits_data": "対左右成績",
        "statcast_data": "Statcast（Baseball Savant）"
    }
    
    now = datetime.now()
    
    for cache_type, description in cache_types.items():
        cache_path = cache_dir / cache_type
        
        if not cache_path.exists():
            results["summary"][cache_type] = "❌ フォルダなし"
            continue
            
        files = list(cache_path.glob("*.json"))
        
        if not files:
            results["summary"][cache_type] = "❌ ファイルなし"
            continue
            
        # 最新と最古のファイルを取得
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        oldest_file = min(files, key=lambda f: f.stat().st_mtime)
        
        latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
        oldest_time = datetime.fromtimestamp(oldest_file.stat().st_mtime)
        
        # 経過時間を計算
        latest_age = now - latest_time
        oldest_age = now - oldest_time
        
        # 状態を判定
        if latest_age.days == 0:
            status = "✅ 今日更新"
        elif latest_age.days == 1:
            status = "⚠️ 昨日更新"
        elif latest_age.days <= 7:
            status = f"⚠️ {latest_age.days}日前"
        else:
            status = f"❌ {latest_age.days}日前"
            
        results["summary"][cache_type] = status
        
        results["details"][cache_type] = {
            "description": description,
            "file_count": len(files),
            "latest_update": latest_time.strftime("%Y/%m/%d %H:%M"),
            "oldest_update": oldest_time.strftime("%Y/%m/%d %H:%M"),
            "latest_file": latest_file.name,
            "status": status
        }
    
    return results

def check_api_endpoints():
    """使用しているAPIエンドポイントを確認"""
    
    api_info = {
        "MLB Stats API": {
            "base_url": "https://statsapi.mlb.com/api/v1",
            "endpoints": {
                "/schedule": "試合スケジュール取得",
                "/teams/{teamId}/roster": "チームロースター取得",
                "/people/{playerId}/stats": "選手統計取得",
                "/people/{playerId}/stats/splits": "対左右成績取得",
                "/teams/{teamId}/stats": "チーム統計取得",
                "/game/{gameId}/boxscore": "試合詳細取得"
            },
            "modules": [
                "src/mlb_api_client.py",
                "scripts/enhanced_stats_collector.py",
                "scripts/bullpen_enhanced_stats.py"
            ]
        },
        "Baseball Savant": {
            "base_url": "https://baseballsavant.mlb.com",
            "endpoints": {
                "/statcast_search": "Barrel%, Hard-Hit%等の取得"
            },
            "modules": [
                "scripts/savant_statcast_fetcher.py"
            ]
        }
    }
    
    return api_info

def check_update_schedule():
    """更新スケジュールを確認"""
    
    schedule = {
        "GitHub Actions": {
            "schedule": "毎日 18:30 JST",
            "workflow": ".github/workflows/daily_mlb_report.yml",
            "actions": [
                "データ取得",
                "レポート生成", 
                "Google Driveアップロード",
                "Discord通知（設定時）"
            ]
        },
        "キャッシュ有効期限": {
            "advanced_stats": "24時間",
            "batting_quality": "24時間",
            "bullpen_stats": "24時間（※現在9日間未更新）",
            "recent_ops": "6時間",
            "splits_data": "24時間",
            "statcast_data": "6時間"
        }
    }
    
    return schedule

def generate_report():
    """レポートを生成"""
    
    print("=" * 60)
    print("MLBデータ分析システム - データ更新状況レポート")
    print("=" * 60)
    print(f"確認日時: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}")
    print()
    
    # キャッシュ状況
    print("【1. キャッシュ更新状況】")
    print("-" * 40)
    
    cache_status = check_cache_status()
    
    for cache_type, status in cache_status["summary"].items():
        detail = cache_status["details"].get(cache_type, {})
        print(f"{status} {cache_type}")
        if detail:
            print(f"    └─ {detail['description']}")
            print(f"       最新: {detail.get('latest_update', 'N/A')}")
            print(f"       ファイル数: {detail.get('file_count', 0)}")
    
    print()
    print("【2. 使用API】")
    print("-" * 40)
    
    api_info = check_api_endpoints()
    for api_name, info in api_info.items():
        print(f"■ {api_name}")
        print(f"  URL: {info['base_url']}")
        print(f"  主要エンドポイント:")
        for endpoint, desc in list(info['endpoints'].items())[:3]:
            print(f"    - {endpoint}: {desc}")
        print()
    
    print("【3. 更新スケジュール】")
    print("-" * 40)
    
    schedule = check_update_schedule()
    for schedule_type, info in schedule.items():
        print(f"■ {schedule_type}")
        if isinstance(info, dict):
            for key, value in info.items():
                if isinstance(value, list):
                    print(f"  {key}:")
                    for item in value:
                        print(f"    - {item}")
                else:
                    print(f"  {key}: {value}")
        print()
    
    print("【4. 問題の診断】")
    print("-" * 40)
    
    # 問題を特定
    problems = []
    
    # bullpen_statsの問題
    if "bullpen_stats" in cache_status["details"]:
        detail = cache_status["details"]["bullpen_stats"]
        if "❌" in detail["status"] or "9日" in detail["status"]:
            problems.append({
                "module": "bullpen_stats",
                "issue": "9日間更新されていない",
                "cause": "APIレスポンス解析エラーの可能性",
                "solution": "bullpen_enhanced_stats.pyの修正が必要"
            })
    
    # エンコーディング問題
    problems.append({
        "module": "全般",
        "issue": "cp932エンコーディングエラー",
        "cause": "選手名の特殊文字（José等）",
        "solution": "UTF-8設定とASCII変換処理の追加"
    })
    
    for i, problem in enumerate(problems, 1):
        print(f"{i}. {problem['module']}")
        print(f"   問題: {problem['issue']}")
        print(f"   原因: {problem['cause']}")
        print(f"   対策: {problem['solution']}")
        print()
    
    print("=" * 60)

if __name__ == "__main__":
    generate_report()
    
    # 個別モジュールのテスト方法も表示
    print("\n【5. 個別モジュールのテスト方法】")
    print("-" * 40)
    print("# bullpen_statsのテスト")
    print("python scripts/bullpen_enhanced_stats.py")
    print()
    print("# 投手統計のテスト")
    print("python scripts/enhanced_stats_collector.py")
    print()
    print("# 打撃統計のテスト")
    print("python scripts/batting_quality_stats.py")
    print()
    print("# MLB APIの直接テスト")
    print("python src/mlb_api_client.py")