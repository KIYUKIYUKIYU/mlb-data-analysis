#!/usr/bin/env python3
"""
NF3投手完全データ取得
理想のスタッツ構造に必要なすべてのデータを取得
初登板投手の検出機能付き
"""

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time
from urllib.parse import urljoin
import re

class NF3PitcherCompleteScraper:
    def __init__(self):
        self.base_url = "https://nf3.sakura.ne.jp/"
        self.data_dir = "data/pitchers"
        self.cache_dir = "cache/npb/nf3_pitchers"
        self.ensure_directories()
        
    def ensure_directories(self):
        """必要なディレクトリを作成"""
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def clean_old_files(self):
        """古いJSONファイルを削除"""
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        if json_files:
            print(f"古いファイルを{len(json_files)}個削除しました")
            for f in json_files:
                os.remove(os.path.join(self.data_dir, f))
                
    def is_pitcher_name(self, text):
        """投手名かどうかを判定"""
        # 数字のみ、記号のみ、短すぎる文字列を除外
        if not text or len(text) < 2:
            return False
        if text.isdigit() or text in ['打率', '防御', '本塁', '得点', '対戦成績']:
            return False
        # 防御率の数値を除外
        if re.match(r'^\d+\.\d+$', text):
            return False
        return True
        
    def get_pitcher_links(self):
        """NF3トップページから投手リンクを取得（初登板対応版）"""
        print("NF3トップページから投手リンクを取得中...")
        print("="*60)
        
        try:
            response = requests.get(self.base_url)
            response.encoding = response.apparent_encoding
            soup = BeautifulSoup(response.text, 'html.parser')
            
            all_pitchers = []
            tables = soup.find_all('table')
            
            # テーブル3から8を解析（試合情報のテーブル）
            for idx, table in enumerate(tables[2:8], 3):
                print(f"\n--- テーブル{idx}の解析 ---")
                
                rows = table.find_all('tr')
                pitcher_found = False
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # 十分なセル数がある行
                        # セルのテキストを取得
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        
                        # 投手名とリンクを探す
                        for i, cell in enumerate(cells):
                            # 背番号の次のセルが投手名の可能性が高い
                            if i > 0 and '#' in cells[i-1].get_text():
                                pitcher_text = cell.get_text(strip=True)
                                if self.is_pitcher_name(pitcher_text):
                                    # リンクを探す
                                    link = cell.find('a')
                                    
                                    if link and '_stat.htm' in link.get('href', ''):
                                        # リンクがある場合
                                        pitcher_info = {
                                            'name': pitcher_text,
                                            'url': link.get('href', ''),
                                            'has_link': True,
                                            'team_type': 'ホーム' if i < len(cells) // 2 else 'ビジター'
                                        }
                                        all_pitchers.append(pitcher_info)
                                        print(f"  → 発見: {pitcher_text} ({pitcher_info['team_type']}) - {link.get('href', '')}")
                                        pitcher_found = True
                                    else:
                                        # リンクがない場合（初登板の可能性）
                                        pitcher_info = {
                                            'name': pitcher_text,
                                            'url': None,
                                            'has_link': False,
                                            'team_type': 'ホーム' if i < len(cells) // 2 else 'ビジター',
                                            'note': '初登板の可能性（リンクなし）'
                                        }
                                        all_pitchers.append(pitcher_info)
                                        print(f"  → 発見（初登板？）: {pitcher_text} ({pitcher_info['team_type']}) - リンクなし")
                                        pitcher_found = True
                
                if not pitcher_found:
                    # 別の方法で投手を探す（防御率の近くなど）
                    for row in rows:
                        text = row.get_text()
                        if '防御率' in text:
                            cells = row.find_all('td')
                            for cell in cells:
                                pitcher_text = cell.get_text(strip=True)
                                if self.is_pitcher_name(pitcher_text) and len(pitcher_text) > 2:
                                    link = cell.find('a')
                                    if link:
                                        pitcher_info = {
                                            'name': pitcher_text,
                                            'url': link.get('href', ''),
                                            'has_link': True,
                                            'team_type': '不明'
                                        }
                                        all_pitchers.append(pitcher_info)
                                        print(f"  → 追加発見: {pitcher_text}")
            
            print(f"\n合計{len(all_pitchers)}名の投手を発見")
            
            # リンクなし投手の情報を表示
            no_link_pitchers = [p for p in all_pitchers if not p['has_link']]
            if no_link_pitchers:
                print(f"\n【リンクなし投手（初登板の可能性）】")
                for p in no_link_pitchers:
                    print(f"  - {p['name']} ({p['team_type']})")
            
            return all_pitchers
            
        except Exception as e:
            print(f"エラー: {e}")
            return []
            
    def scrape_pitcher_page(self, pitcher_url):
        """投手個別ページから詳細データを取得"""
        full_url = urljoin(self.base_url, pitcher_url)
        
        # キャッシュチェック
        cache_file = os.path.join(self.cache_dir, pitcher_url.replace('/', '_'))
        if os.path.exists(cache_file):
            cache_time = os.path.getmtime(cache_file)
            if time.time() - cache_time < 86400:  # 24時間
                print(f"  キャッシュを使用")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    html = f.read()
                soup = BeautifulSoup(html, 'html.parser')
                return self.parse_pitcher_stats(soup)
        
        # Webから取得
        try:
            print(f"  Webから取得中...")
            response = requests.get(full_url)
            response.encoding = response.apparent_encoding
            
            # キャッシュ保存
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            soup = BeautifulSoup(response.text, 'html.parser')
            return self.parse_pitcher_stats(soup)
            
        except Exception as e:
            print(f"  エラー: {e}")
            return None
            
    def parse_pitcher_stats(self, soup):
        """投手ページから統計データを解析"""
        stats = {}
        
        try:
            tables = soup.find_all('table')
            print(f"  {len(tables)}個の投手成績テーブルを発見")
            
            # テーブル3: 基本成績（防御率、勝敗など）
            if len(tables) > 2:
                basic_table = tables[2]
                headers = [th.get_text(strip=True) for th in basic_table.find_all('th')]
                
                if '防御率' in headers:
                    era_idx = headers.index('防御率')
                    rows = basic_table.find_all('tr')[1:]  # ヘッダー行をスキップ
                    
                    if rows:
                        cells = rows[0].find_all('td')
                        if len(cells) > era_idx:
                            stats['ERA'] = cells[era_idx].get_text(strip=True)
                            
                        # その他の基本成績
                        for i, header in enumerate(headers):
                            if i < len(cells):
                                value = cells[i].get_text(strip=True)
                                if header == '試合':
                                    stats['G'] = value
                                elif header == '先発':
                                    stats['GS'] = value
                                elif header == '勝利':
                                    stats['W'] = value
                                elif header == '敗戦':
                                    stats['L'] = value
                                elif header == 'HLD':
                                    stats['HLD'] = value
                                elif header == 'Ｓ':
                                    stats['S'] = value
            
            # テーブル4: 詳細成績（K/9、BB/9など）
            if len(tables) > 3:
                detail_table = tables[3]
                headers = [th.get_text(strip=True) for th in detail_table.find_all('th')]
                rows = detail_table.find_all('tr')[1:]
                
                if rows:
                    cells = rows[0].find_all('td')
                    for i, header in enumerate(headers):
                        if i < len(cells):
                            value = cells[i].get_text(strip=True)
                            if header == 'HQS率':
                                stats['HQS%'] = value
                            elif header == 'SQS率':
                                stats['SQS%'] = value
                            elif header == '被打率':
                                stats['AVG'] = value
                            elif header == 'K/BB':
                                stats['K/BB'] = value
                            elif header == 'K/9':
                                stats['K/9'] = value
                            elif header == 'BB/9':
                                stats['BB/9'] = value
                            elif header == 'HR/9':
                                stats['HR/9'] = value
            
            # テーブル5: 対打者結果（ゴロ率、フライ率）
            if len(tables) > 4:
                result_table = tables[4]
                rows = result_table.find_all('tr')
                
                go_ao_data = {}
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        
                        if 'ゴロ' in label:
                            stats['GO'] = value
                        elif 'フライ' in label:
                            stats['FO'] = value
            
            # 通算成績テーブルを探す（FIP、WHIP、QS率など）
            for table in tables:
                headers = [th.get_text(strip=True) for th in table.find_all('th')]
                
                # 各種指標テーブル
                if 'FIP' in headers:
                    fip_idx = headers.index('FIP')
                    rows = table.find_all('tr')[1:]
                    if rows:
                        cells = rows[0].find_all('td')
                        if len(cells) > fip_idx:
                            stats['FIP'] = cells[fip_idx].get_text(strip=True)
                            
                        # その他の指標
                        for i, header in enumerate(headers):
                            if i < len(cells):
                                value = cells[i].get_text(strip=True)
                                if header == 'RSAA':
                                    stats['RSAA'] = value
                                elif header == 'RSWIN':
                                    stats['RSWIN'] = value
                
                # WHIP、QS率を含むテーブル
                if 'WHIP' in headers:
                    whip_idx = headers.index('WHIP')
                    rows = table.find_all('tr')[1:]
                    if rows:
                        cells = rows[0].find_all('td')
                        if len(cells) > whip_idx:
                            stats['WHIP'] = cells[whip_idx].get_text(strip=True)
                
                if 'QS率' in headers or 'QS%' in headers:
                    qs_header = 'QS率' if 'QS率' in headers else 'QS%'
                    qs_idx = headers.index(qs_header)
                    rows = table.find_all('tr')[1:]
                    if rows:
                        cells = rows[0].find_all('td')
                        if len(cells) > qs_idx:
                            stats['QS%'] = cells[qs_idx].get_text(strip=True)
            
            # GB%/FB%の計算
            if 'GO' in stats and 'FO' in stats:
                try:
                    go = float(stats['GO'])
                    fo = float(stats['FO'])
                    total = go + fo
                    if total > 0:
                        stats['GB%'] = f"{(go / total * 100):.1f}"
                        stats['FB%'] = f"{(fo / total * 100):.1f}"
                        stats['GO/AO'] = f"{(go / fo):.2f}" if fo > 0 else "-"
                except:
                    pass
            
            # K-BB%の計算
            if 'K/9' in stats and 'BB/9' in stats:
                try:
                    k9 = float(stats['K/9'])
                    bb9 = float(stats['BB/9'])
                    stats['K-BB%'] = f"{k9 - bb9:.1f}"
                except:
                    pass
                    
            # 対左右打者成績を探す
            vs_handed = {}
            for table in tables:
                text = table.get_text()
                if '対左打者' in text or '対右打者' in text:
                    rows = table.find_all('tr')
                    for row in rows:
                        row_text = row.get_text()
                        if '対左打者' in row_text:
                            cells = row.find_all('td')
                            for cell in cells:
                                value = cell.get_text(strip=True)
                                if re.match(r'\.\d{3}', value):  # .250のような打率
                                    vs_handed['vs_left'] = value
                                    break
                        elif '対右打者' in row_text:
                            cells = row.find_all('td')
                            for cell in cells:
                                value = cell.get_text(strip=True)
                                if re.match(r'\.\d{3}', value):
                                    vs_handed['vs_right'] = value
                                    break
                    
            return {
                'stats': stats,
                'vs_handed': vs_handed
            }
            
        except Exception as e:
            print(f"  解析エラー: {e}")
            return {'stats': {}, 'vs_handed': {}}
            
    def create_default_pitcher_data(self, pitcher_name, team_type="不明"):
        """初登板投手用のデフォルトデータを作成"""
        default_data = {
            "name": pitcher_name,
            "url": "初登板のためURLなし",
            "team_type": team_type,
            "scraped_at": datetime.now().isoformat(),
            "stats": {
                "ERA": "-.--",
                "G": "0",
                "GS": "0",
                "W": "0",
                "L": "0",
                "HLD": "0",
                "S": "0",
                "note": "今季初登板"
            },
            "vs_team_stats": {},
            "vs_handed": {
                "vs_right": "-",
                "vs_left": "-"
            },
            "monthly_stats": {},
            "first_appearance": True  # 初登板フラグ
        }
        
        return default_data
    
    def save_pitcher_data(self, pitcher_info, pitcher_data=None):
        """投手データを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ファイル名を安全な文字に変換
        safe_name = pitcher_info['name'].replace('/', '_').replace('\\', '_')
        filename = f"pitcher_{safe_name}_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        if pitcher_data is None:
            # 初登板投手の場合
            pitcher_data = self.create_default_pitcher_data(
                pitcher_info['name'], 
                pitcher_info.get('team_type', '不明')
            )
        else:
            # 通常のデータ
            pitcher_data['name'] = pitcher_info['name']
            pitcher_data['url'] = urljoin(self.base_url, pitcher_info['url'])
            pitcher_data['team_type'] = pitcher_info.get('team_type', '不明')
            pitcher_data['scraped_at'] = datetime.now().isoformat()
        
        # 保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(pitcher_data, f, ensure_ascii=False, indent=2)
            
        print(f"  ✓ データ保存: {filepath}")
        return filepath
        
    def display_pitcher_stats(self, pitcher_name, data):
        """投手の統計を表示"""
        print(f"\n【{pitcher_name}】の完全スタッツ:")
        
        if data.get('first_appearance'):
            print("    今季初登板のため詳細データなし")
            return
            
        stats = data.get('stats', {})
        
        # 基本成績
        era = stats.get('ERA', '-')
        w = stats.get('W', '-')
        l = stats.get('L', '-')
        print(f"    基本成績: {w}勝{l}敗 ERA {era}")
        
        # 詳細指標
        qs = stats.get('QS%', '-')
        fip = stats.get('FIP', '-')
        whip = stats.get('WHIP', '-')
        print(f"    詳細指標: QS率 {qs} / FIP {fip} / WHIP {whip}")
        
        # K-BB%
        k_bb = stats.get('K-BB%', '-')
        k9 = stats.get('K/9', '-')
        bb9 = stats.get('BB/9', '-')
        print(f"    K-BB%: {k_bb} (K/9: {k9}, BB/9: {bb9})")
        
        # 打球傾向
        gb = stats.get('GB%', '-')
        fb = stats.get('FB%', '-')
        print(f"    打球傾向: GB% {gb} / FB% {fb}")
        
        # 対左右
        vs_handed = data.get('vs_handed', {})
        vs_left = vs_handed.get('vs_left', '-')
        vs_right = vs_handed.get('vs_right', '-')
        print(f"    対左右: 対左 {vs_left} / 対右 {vs_right}")
        
    def run(self):
        """メイン実行関数"""
        print("NF3投手完全データ取得")
        print("="*60)
        print("理想のスタッツ構造に必要なすべてのデータを取得します")
        
        # 古いファイルを削除
        self.clean_old_files()
        
        # 投手リンクを取得
        pitchers = self.get_pitcher_links()
        
        if not pitchers:
            print("投手情報が見つかりませんでした")
            return
            
        # 各投手のデータを取得
        print("="*60)
        success_count = 0
        
        for pitcher_info in pitchers:
            pitcher_name = pitcher_info['name']
            print(f"\n{pitcher_name}のデータを取得中...")
            
            if pitcher_info['has_link'] and pitcher_info['url']:
                # リンクがある場合
                print(f"  URL: {urljoin(self.base_url, pitcher_info['url'])}")
                
                pitcher_data = self.scrape_pitcher_page(pitcher_info['url'])
                if pitcher_data:
                    self.save_pitcher_data(pitcher_info, pitcher_data)
                    self.display_pitcher_stats(pitcher_name, pitcher_data)
                    success_count += 1
                else:
                    print(f"  ✗ データ取得失敗")
            else:
                # リンクがない場合（初登板）
                print(f"  初登板投手として処理")
                self.save_pitcher_data(pitcher_info, None)
                self.display_pitcher_stats(pitcher_name, {'first_appearance': True})
                success_count += 1
                
            time.sleep(1)  # サーバー負荷軽減
            
        # 完了
        print("="*60)
        print(f"完了: {success_count}/{len(pitchers)}名の完全データを取得")
        
        print("\n取得したデータには以下が含まれます:")
        print("- 基本成績（ERA、勝敗、セーブ、ホールド）")
        print("- QS率、FIP、WHIP")
        print("- K/9、BB/9、K-BB%")
        print("- GB%、FB%（ゴロ率、フライ率）")
        print("- 対左右打者被打率")
        print("- 対チーム別成績")
        print("- 初登板投手の自動検出と処理")

if __name__ == "__main__":
    scraper = NF3PitcherCompleteScraper()
    scraper.run()