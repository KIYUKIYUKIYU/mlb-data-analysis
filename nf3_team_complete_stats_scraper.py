#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NF3 team_etc.htmから全チーム統計を取得
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from typing import Dict, List

class NF3TeamCompleteStatsScraper:
    def __init__(self):
        self.url = "https://nf3.sakura.ne.jp/Stats/team_etc.htm"
        self.data_dir = "data/nf3_complete"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def scrape_all_stats(self):
        """全チーム統計を取得"""
        print("=== NF3 チーム完全統計取得 ===")
        print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        response = requests.get(self.url, timeout=10)
        if response.status_code != 200:
            print(f"エラー: ステータス {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        print(f"テーブル数: {len(tables)}")
        
        results = {
            "central": {},  # セ・リーグ
            "pacific": {}   # パ・リーグ
        }
        
        # セ・リーグ打撃統計（テーブル0）
        if len(tables) > 0:
            print("\n=== セ・リーグ打撃統計 ===")
            results["central"]["batting"] = self.parse_batting_table(tables[0])
        
        # セ・リーグ打撃詳細統計（テーブル1）
        if len(tables) > 1:
            print("\n=== セ・リーグ打撃詳細統計 ===")
            results["central"]["batting_advanced"] = self.parse_batting_advanced_table(tables[1])
        
        # セ・リーグ投手統計（テーブル2）
        if len(tables) > 2:
            print("\n=== セ・リーグ投手統計 ===")
            results["central"]["pitching"] = self.parse_pitching_table(tables[2])
        
        # セ・リーグ投手詳細統計（テーブル3）
        if len(tables) > 3:
            print("\n=== セ・リーグ投手詳細統計 ===")
            results["central"]["pitching_advanced"] = self.parse_pitching_advanced_table(tables[3])
        
        # パ・リーグ打撃統計（テーブル4）
        if len(tables) > 4:
            print("\n=== パ・リーグ打撃統計 ===")
            results["pacific"]["batting"] = self.parse_batting_table(tables[4])
        
        # パ・リーグ打撃詳細統計（テーブル5）
        if len(tables) > 5:
            print("\n=== パ・リーグ打撃詳細統計 ===")
            results["pacific"]["batting_advanced"] = self.parse_batting_advanced_table(tables[5])
        
        # パ・リーグ投手統計（テーブル6）
        if len(tables) > 6:
            print("\n=== パ・リーグ投手統計 ===")
            results["pacific"]["pitching"] = self.parse_pitching_table(tables[6])
        
        # パ・リーグ投手詳細統計（テーブル7）
        if len(tables) > 7:
            print("\n=== パ・リーグ投手詳細統計 ===")
            results["pacific"]["pitching_advanced"] = self.parse_pitching_advanced_table(tables[7])
        
        # 結果を保存
        output_file = os.path.join(self.data_dir, "team_complete_stats.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n結果を保存: {output_file}")
        
        # サマリーを表示
        self.display_summary(results)
        
        return results
    
    def parse_batting_table(self, table) -> Dict:
        """打撃統計テーブルを解析"""
        stats = {}
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # ヘッダーをスキップ
            cells = row.find_all(['td', 'th'])
            if len(cells) > 6:
                team_name = cells[0].text.strip()
                if team_name and team_name != "チーム名":
                    stats[team_name] = {
                        "batting_avg": cells[1].text.strip(),
                        "games": cells[2].text.strip(),
                        "plate_appearances": cells[3].text.strip(),
                        "at_bats": cells[4].text.strip(),
                        "runs": cells[5].text.strip(),
                        "hits": cells[6].text.strip()
                    }
                    # 本塁打を探す（通常は位置10-13あたり）
                    if len(cells) > 13:
                        stats[team_name]["home_runs"] = cells[13].text.strip()
                    
                    print(f"  {team_name}: 打率 {stats[team_name]['batting_avg']}, 得点 {stats[team_name]['runs']}")
        
        return stats
    
    def parse_batting_advanced_table(self, table) -> Dict:
        """打撃詳細統計テーブルを解析"""
        stats = {}
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # ヘッダーをスキップ
            cells = row.find_all(['td', 'th'])
            if len(cells) > 3:
                team_name = cells[0].text.strip()
                if team_name and team_name != "チーム名":
                    stats[team_name] = {
                        "obp": cells[1].text.strip(),  # 出塁率
                        "slg": cells[2].text.strip(),  # 長打率
                        "ops": cells[3].text.strip()   # OPS
                    }
                    print(f"  {team_name}: OPS {stats[team_name]['ops']}")
        
        return stats
    
    def parse_pitching_table(self, table) -> Dict:
        """投手統計テーブルを解析"""
        stats = {}
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # ヘッダーをスキップ
            cells = row.find_all(['td', 'th'])
            if len(cells) > 1:
                team_name = cells[0].text.strip()
                if team_name and team_name != "チーム名":
                    stats[team_name] = {
                        "era": cells[1].text.strip(),  # 防御率
                        "games": cells[2].text.strip() if len(cells) > 2 else "",
                        "wins": cells[3].text.strip() if len(cells) > 3 else "",
                        "losses": cells[4].text.strip() if len(cells) > 4 else ""
                    }
                    print(f"  {team_name}: 防御率 {stats[team_name]['era']}")
        
        return stats
    
    def parse_pitching_advanced_table(self, table) -> Dict:
        """投手詳細統計テーブルを解析"""
        stats = {}
        rows = table.find_all('tr')
        
        for row in rows[1:]:  # ヘッダーをスキップ
            cells = row.find_all(['td', 'th'])
            if len(cells) > 2:
                team_name = cells[0].text.strip()
                if team_name and team_name != "チーム名":
                    stats[team_name] = {
                        "whip": cells[1].text.strip(),
                        "qs_rate": cells[2].text.strip() if len(cells) > 2 else ""
                    }
                    print(f"  {team_name}: WHIP {stats[team_name]['whip']}")
        
        return stats
    
    def display_summary(self, results):
        """サマリーを表示"""
        print("\n=== 防御率ランキング ===")
        all_teams = []
        
        # セ・リーグ
        if "central" in results and "pitching" in results["central"]:
            for team, stats in results["central"]["pitching"].items():
                if "era" in stats:
                    try:
                        era = float(stats["era"])
                        all_teams.append((team, era, "セ"))
                    except:
                        pass
        
        # パ・リーグ
        if "pacific" in results and "pitching" in results["pacific"]:
            for team, stats in results["pacific"]["pitching"].items():
                if "era" in stats:
                    try:
                        era = float(stats["era"])
                        all_teams.append((team, era, "パ"))
                    except:
                        pass
        
        # ソート
        all_teams.sort(key=lambda x: x[1])
        
        for rank, (team, era, league) in enumerate(all_teams, 1):
            print(f"{rank:2d}. {team}（{league}）: {era:.2f}")

if __name__ == "__main__":
    scraper = NF3TeamCompleteStatsScraper()
    scraper.scrape_all_stats()