"""
明日の試合の純粋なデータ比較（予想判定なし）
"""
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from src.mlb_api_client import MLBApiClient

def load_latest_data(team_id, data_type):
    """最新のデータファイルを読み込む"""
    if data_type == "stats":
        pattern = f"team_analysis_{team_id}_*.json"
        dir_path = Path("data/processed")
    elif data_type == "recent_ops":
        pattern = f"team_{team_id}_last10games_*.json"
        dir_path = Path("data/processed/recent_ops")
    elif data_type == "rates":
        pattern = f"team_{team_id}_rates_*.json"
        dir_path = Path("data/processed/accurate_rates")
    else:
        return None
    
    files = list(dir_path.glob(pattern))
    if not files:
        return None
    
    latest_file = max(files, key=lambda x: x.stat().st_mtime)
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_percentage(value):
    """パーセンテージ表示のフォーマット"""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"

def format_decimal(value, decimals=3):
    """小数点表示のフォーマット"""
    if value is None:
        return "N/A"
    # 文字列の場合は数値に変換
    if isinstance(value, str):
        try:
            value = float(value)
        except:
            return value
    return f"{value:.{decimals}f}"

def create_comparison_report(game_info, team1_data, team2_data):
    """比較レポートの作成"""
    team1 = game_info['teams']['away']['team']['name']
    team2 = game_info['teams']['home']['team']['name']
    
    report = {
        "game_info": {
            "date": game_info['gameDate'],
            "venue": game_info.get('venue', {}).get('name', 'Unknown'),
            "away_team": team1,
            "home_team": team2
        },
        "team_stats": {},
        "comparison_data": []
    }
    
    # チーム統計の基本情報
    for team_name, team_data in [(team1, team1_data), (team2, team2_data)]:
        stats = team_data.get('stats', {})
        recent_ops = team_data.get('recent_ops', {})
        rates = team_data.get('rates', {})
        
        # battingデータの取得方法を修正
        batting_data = stats.get('batting', {})
        
        # 打率の処理
        batting_avg_str = batting_data.get('avg', '')
        if isinstance(batting_avg_str, str) and batting_avg_str.startswith('.'):
            batting_avg = float(batting_avg_str)
        else:
            batting_avg = None
            
        # OPSの処理
        ops_value = batting_data.get('ops')
        if isinstance(ops_value, str) and ops_value.startswith('.'):
            ops_value = float(ops_value)
            
        report["team_stats"][team_name] = {
            "打撃": {
                "打率": format_decimal(batting_avg),
                "OPS": format_decimal(ops_value),
                "直近10試合OPS": format_decimal(recent_ops.get('team_average_ops')),
                "得点/試合": format_decimal(batting_data.get('runs', 0) / 70 if batting_data.get('runs') else None, 2),  # 仮に70試合で計算
                "本塁打": batting_data.get('home_runs', 'N/A'),
                "三振率": format_percentage(rates.get('team_batting', {}).get('k_percentage')),
                "四球率": format_percentage(rates.get('team_batting', {}).get('bb_percentage')),
                "ISO": format_decimal(rates.get('team_batting', {}).get('iso'))
            },
            "投手": {
                "防御率": format_decimal(stats.get('pitching', {}).get('bullpenAggregate', {}).get('era'), 2),
                "WHIP": format_decimal(rates.get('team_pitching', {}).get('whip'), 2),
                "三振率": format_percentage(rates.get('team_pitching', {}).get('k_percentage')),
                "四球率": format_percentage(rates.get('team_pitching', {}).get('bb_percentage')),
                "ゴロ率": format_percentage(rates.get('team_pitching', {}).get('gb_percentage')),
                "QS率": format_percentage(stats.get('qs_rate'))
            }
        }
    
    # 比較データの作成
    comparison_categories = [
        ("打撃指標", [
            ("打率", "batting_avg", "higher"),
            ("OPS", "ops", "higher"),
            ("直近10試合OPS", "recent_ops", "higher"),
            ("得点/試合", "runs_per_game", "higher"),
            ("本塁打", "home_runs", "higher")
        ]),
        ("投手指標", [
            ("防御率", "era", "lower"),
            ("WHIP", "whip", "lower"),
            ("QS率", "qs_rate", "higher")
        ]),
        ("率統計", [
            ("打者三振率", "batting_k_rate", "lower"),
            ("打者四球率", "batting_bb_rate", "higher"),
            ("投手三振率", "pitching_k_rate", "higher"),
            ("投手四球率", "pitching_bb_rate", "lower")
        ])
    ]
    
    for category, metrics in comparison_categories:
        category_data = {"category": category, "metrics": []}
        
        for metric_name, metric_key, better in metrics:
            value1 = get_metric_value(team1_data, metric_key)
            value2 = get_metric_value(team2_data, metric_key)
            
            category_data["metrics"].append({
                "name": metric_name,
                "team1_value": format_value(value1, metric_key),
                "team2_value": format_value(value2, metric_key),
                "difference": calculate_difference(value1, value2, better)
            })
        
        report["comparison_data"].append(category_data)
    
    return report

def get_metric_value(team_data, metric_key):
    """メトリクス値の取得"""
    stats = team_data.get('stats', {})
    
    if metric_key == "recent_ops":
        return team_data.get('recent_ops', {}).get('team_average_ops')
    elif metric_key == "batting_k_rate":
        return team_data.get('rates', {}).get('team_batting', {}).get('k_percentage')
    elif metric_key == "batting_bb_rate":
        return team_data.get('rates', {}).get('team_batting', {}).get('bb_percentage')
    elif metric_key == "pitching_k_rate":
        return team_data.get('rates', {}).get('team_pitching', {}).get('k_percentage')
    elif metric_key == "pitching_bb_rate":
        return team_data.get('rates', {}).get('team_pitching', {}).get('bb_percentage')
    elif metric_key == "whip":
        return team_data.get('rates', {}).get('team_pitching', {}).get('whip')
    elif metric_key == "batting_avg":
        batting_avg = stats.get('batting', {}).get('avg', '')
        if isinstance(batting_avg, str) and batting_avg.startswith('.'):
            return float(batting_avg)
        return None
    elif metric_key == "ops":
        ops_value = stats.get('batting', {}).get('ops')
        if isinstance(ops_value, str) and ops_value.startswith('.'):
            return float(ops_value)
        return ops_value
    elif metric_key == "runs_per_game":
        runs = stats.get('batting', {}).get('runs', 0)
        return runs / 70 if runs else None  # 仮に70試合で計算
    elif metric_key == "home_runs":
        return stats.get('batting', {}).get('home_runs')
    elif metric_key == "era":
        return stats.get('pitching', {}).get('bullpenAggregate', {}).get('era')
    else:
        return stats.get(metric_key)

def format_value(value, metric_key):
    """値のフォーマット"""
    if value is None:
        return "N/A"
    
    if "rate" in metric_key or metric_key == "qs_rate":
        return format_percentage(value)
    elif metric_key in ["batting_avg", "ops", "recent_ops", "era", "whip", "iso"]:
        decimals = 2 if metric_key == "era" else 3
        return format_decimal(value, decimals)
    elif metric_key in ["home_runs", "runs_per_game"]:
        if metric_key == "runs_per_game":
            return format_decimal(value, 2)
        return str(value)
    else:
        return str(value)

def calculate_difference(value1, value2, better="higher"):
    """差分の計算（純粋な数値差のみ）"""
    if value1 is None or value2 is None:
        return None
    
    try:
        # 文字列の場合は数値に変換
        if isinstance(value1, str):
            value1 = float(value1)
        if isinstance(value2, str):
            value2 = float(value2)
        
        diff = float(value1) - float(value2)
        return round(diff, 3)
    except:
        return None

def save_comparison(report, timestamp):
    """比較結果の保存"""
    output_dir = Path("data/comparisons")
    output_dir.mkdir(exist_ok=True)
    
    filename = f"comparison_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"比較データを保存: {filepath}")
    return filepath

def print_comparison_report(report):
    """比較レポートの表示"""
    print("\n" + "="*80)
    print("MLB 試合データ比較")
    print("="*80)
    
    game_info = report['game_info']
    print(f"\n日時: {game_info['date']}")
    print(f"球場: {game_info['venue']}")
    print(f"対戦: {game_info['away_team']} @ {game_info['home_team']}")
    
    # チーム統計の表示
    print("\n" + "-"*80)
    print("チーム統計")
    print("-"*80)
    
    for team_name, stats in report['team_stats'].items():
        print(f"\n【{team_name}】")
        for category, metrics in stats.items():
            print(f"\n{category}:")
            for metric_name, value in metrics.items():
                print(f"  {metric_name}: {value}")
    
    # 比較データの表示
    print("\n" + "-"*80)
    print("データ比較")
    print("-"*80)
    
    for category_data in report['comparison_data']:
        print(f"\n【{category_data['category']}】")
        print(f"{'指標':<15} {game_info['away_team']:<20} {game_info['home_team']:<20} {'差':<10}")
        print("-" * 70)
        
        for metric in category_data['metrics']:
            diff_str = ""
            if metric['difference'] is not None:
                diff_str = f"{metric['difference']:+.3f}"
            
            print(f"{metric['name']:<15} {metric['team1_value']:<20} {metric['team2_value']:<20} {diff_str:<10}")

def main():
    print("MLB 純粋データ比較システム")
    print("=" * 50)
    
    client = MLBApiClient()
    
    # 明日の日付を取得（米国東部時間基準）
    jst_now = datetime.now()
    et_now = jst_now - timedelta(hours=13)
    
    # 日本時間の午後1時前ならMLBはまだ前日
    if jst_now.hour < 13:
        date_str = et_now.strftime('%Y-%m-%d')
    else:
        date_str = (et_now + timedelta(days=1)).strftime('%Y-%m-%d')
    
    print(f"対象日付: {date_str} (ET)")
    
    # 明日の試合を取得（_make_requestを使用）
    games = client._make_request(f"schedule?sportId=1&date={date_str}")
    
    if not games or 'dates' not in games or not games['dates']:
        print("明日の試合はありません")
        return
    
    game_list = games['dates'][0]['games']
    print(f"\n{len(game_list)}試合が予定されています")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_reports = []
    
    for i, game in enumerate(game_list, 1):
        print(f"\n[{i}/{len(game_list)}] 処理中...")
        
        away_team_id = game['teams']['away']['team']['id']
        home_team_id = game['teams']['home']['team']['id']
        
        print(f"  Away: {game['teams']['away']['team']['name']} (ID: {away_team_id})")
        print(f"  Home: {game['teams']['home']['team']['name']} (ID: {home_team_id})")
        
        # 各チームのデータを読み込む
        away_data = {
            'stats': load_latest_data(away_team_id, 'stats'),
            'recent_ops': load_latest_data(away_team_id, 'recent_ops'),
            'rates': load_latest_data(away_team_id, 'rates')
        }
        
        home_data = {
            'stats': load_latest_data(home_team_id, 'stats'),
            'recent_ops': load_latest_data(home_team_id, 'recent_ops'),
            'rates': load_latest_data(home_team_id, 'rates')
        }
        
        # データが揃っているか確認
        if not away_data['stats']:
            print(f"  ⚠️ Away team stats missing")
        if not home_data['stats']:
            print(f"  ⚠️ Home team stats missing")
            
        if not all([away_data['stats'], home_data['stats']]):
            print(f"  ⚠️ データ不足のためスキップ")
            continue
        
        # 比較レポート作成
        report = create_comparison_report(game, away_data, home_data)
        all_reports.append(report)
        
        # レポート表示
        print_comparison_report(report)
    
    # 全試合のレポートを保存
    if all_reports:
        summary_file = save_comparison({
            'date': date_str,
            'total_games': len(all_reports),
            'comparisons': all_reports
        }, timestamp)
        
        print(f"\n全{len(all_reports)}試合の比較完了")
        print(f"サマリーファイル: {summary_file}")

if __name__ == "__main__":
    main()