# MLB Data Analysis Project

MLB試合データを自動収集・分析し、日本時間19:30に予想レポートを生成するシステムです。  
本 README は **現状の実装・運用**に合わせて最新化しています。

---

## 目次
- プロジェクト概要
- 開発ルール（⚠️厳守）
- システム構成（データフロー）
- セットアップ
- 使い方（cmd.exe）
- 出力物
- データ契約 v0.1（現行出力準拠）
- よくある質問 / トラブルシューティング

---

## プロジェクト概要

### 主な機能
- 自動データ収集: MLB Stats API から試合・選手データを取得
- 統計分析: ERA, FIP, xFIP, WHIP 等の高度指標を **計算し、レポートに出力**（※JSON化では**再計算しません**）
- レポート生成: **テキスト / HTML /（任意で PDF）** 形式で出力
- 自動実行: GitHub Actions で毎日 **19:30（JST）** に実行（運用方針）
- （任意）Google Drive 連携でレポートを保存

> ここでいう「高度指標の計算」は、既存スクリプト群で実行・レポートに反映済みの値を指します。  
> **JSON生成段階では再計算せず**、レポート/HTMLなど**既に確定している値をパススルー**します。

### 生成されるレポート内容（例）
- 試合予想と分析
- 先発投手の詳細統計（ERA / FIP / xFIP / WHIP / K-BB% / GB% / FB% / QS% / SwStr% / BABIP / 対左右OPS など）
- チーム打撃成績（シーズン、対左右、xwOBA、Barrel%、Hard-Hit%、**過去5/10試合OPS** など）
- 中継ぎ陣の状態（人数、ERA、FIP、xFIP、WHIP、K-BB%、役割、疲労コメント）
- データ信頼性スコア（0/4〜4/4）

---

## ⚠️ 開発ルール（絶対遵守）

1. **既存コード確認** → 影響範囲を列挙  
2. **ファイルは全文提示**（部分差分ではなく、丸ごと貼れる形）  
3. **Windows 11 / cmd.exe 前提**（PowerShell/Unix系コマンド禁止）  
4. **実行手順は cmd.exe でコピペ可**にする  
5. **“ないなら出さない”**（未取得の項目は無理に生成しない）

---

## システム構成（データフロー）

curated/_meta
└──（既存レポートが利用する生データ一式）

build_model.py
└── models/mlb_daily_YYYYMMDD.json を生成
（※数値は再計算せず、既存のレポート/HTML 等「確実に更新済みの値」を
そのままデータ化する＝パススルー）

render_report.py + templates/mlb_daily.txt.j2
└── daily_reports/MLBYYYY-MM-DD.txt を出力

convert_to_html.py（任意）
└── 上記 TXT を HTML に変換（PDF 変換スクリプトも任意で利用可）

yaml
コピーする
編集する

- **重要**：本ラインでは **“ないなら出さない”** を徹底。未取得の項目は **省略** します。  
- 変換系スクリプト（`convert_to_html.py` など）はリポジトリに存在します。

---

## セットアップ

- Python 3.10+ 推奨
- 仮想環境（venv）
- 依存関係: `pip install -r requirements.txt`

---

## 使い方（cmd.exe）

**例：2025-08-25 のレポートを作る場合**

```bat
:: 1) プロジェクトへ移動
cd C:\path\to\mlb-data-analysis

:: 2) 仮想環境アクティベート
.\venv\Scripts\activate

:: 3) 依存パッケージ（必要なら）
pip install -r requirements.txt

:: 4) JSONモデル生成（再計算なし／パススルー）
python build_model.py --date 2025-08-25

:: 5) テキストレポート出力（Jinja2 テンプレ使用）
python render_report.py --date 2025-08-25

:: 6) HTML 変換（任意）
python convert_to_html.py --in daily_reports\MLB2025-08-25.txt --out reports\MLB2025-08-25.html
スクリプト引数は環境に合わせて調整してください。

出力物
models/mlb_daily_YYYYMMDD.json … パススルー JSON（再計算なし）

daily_reports/MLBYYYY-MM-DD.txt … テキストレポート

reports/MLBYYYY-MM-DD.html … HTML（任意）

PDF（任意）

データ契約 v0.1（現行出力準拠）
方針： 現在レポート／HTMLに実際に表示されている項目だけを JSON に載せる。
“ないなら出さない（省略）”。再計算はしない。

トップレベル
generated_at (ISO8601), date (YYYY-MM-DD), timezone, games_count, source_meta, games[]

games[]（抜粋）
game_id, league, season, status, start_time_local, start_time_utc, venue

matchup: away_team, home_team

starters:

away, home:

name, hand, probable

season: （レポートに出ている範囲の指標のみ）

省略: last_5_starts

vs_opponent: 今季のみ（出ていなければ省略）

bullpens:

away, home: count, era, fip, xfip, whip, kbb_pct, 役割メモ、疲労コメント など（出ている範囲のみ）

key_relievers: 最大 5 名（出ていれば）

batting:

season 指標、vs_lhp / vs_rhp、xwOBA、Barrel%、Hard-Hit%

last_5_games.ops / last_10_games.ops（出ていれば）

form / notes：出ていれば

表示フォーマット（テンプレ側の丸め）
OPS/OBP/SLG/ISO：小数第3位

ERA/FIP/xFIP/WHIP：小数第2位

%系：小数1位 + %

RPG：小数1位

よくある質問 / トラブルシューティング
高度指標はどこで計算している？
→ 既存の解析スクリプト群で算出し、レポートに出力しています。JSON化では再計算しません。

last_5_starts を入れない理由は？
→ 現行レポートに項目が無いため。“ないなら出さない” ポリシーに従います。

HTML/PDF 変換は？
→ convert_to_html.py 等を利用してください（PDF は任意の変換スクリプトを使用可能）。

yaml
コピーする
編集する

---

必要なら、この後 **`build_model.py` / `render_report.py`** の“パススルー実装（全文）”とコマンドも続けて出します。
::contentReference[oaicite:0]{index=0}