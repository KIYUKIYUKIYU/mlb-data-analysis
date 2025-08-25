# 🤖 AIアシスタント（Claude/ChatGPT等）への標準指示書

このドキュメントをAIアシスタントとの会話の最初にコピー＆ペーストしてください。

---

## 📋 **プロジェクト情報**

```
プロジェクト名: MLB Data Analysis
リポジトリ: https://github.com/KIYUKIYUKIYU/mlb-data-analysis
目的: MLB試合データの自動収集・分析・レポート生成
言語: Python 3.10+
実行環境: Windows 11, GitHub Actions
```

## 🔴 **重要な約束事**

**あなたは以下のルールを厳守してください：**

1. **新しいコードを書く前に、必ず既存コードの確認を要求する**
2. **既存のデータ構造を変更しない**
3. **既存の関数シグネチャを維持する**
4. **エラーハンドリングパターンを統一する**
5. **プロジェクトの命名規則に従う**

## 📁 **確認すべき主要ファイル**

新しいコードを生成する前に、以下のファイルの確認を求めてください：

```
主要ファイルのURL:
- https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/scripts/mlb_complete_report_real.py
- https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/src/mlb_api_client.py
- https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/scripts/convert_to_html.py
- https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/scripts/fetch_all_mlb_pitchers.py
```

## 🏗️ **プロジェクト構造**

```
mlb-data-analysis/
├── src/
│   └── mlb_api_client.py       # MLB API クライアント
├── scripts/
│   ├── mlb_complete_report_real.py  # メインレポート生成
│   ├── convert_to_html.py          # HTML変換
│   ├── convert_to_pdf.py           # PDF変換
│   └── fetch_all_mlb_pitchers.py   # 投手データ取得
├── cache/pitcher_info/          # 投手情報キャッシュ
├── daily_reports/               # 生成レポート
└── core/                        # コアモジュール（開発中）
```

## 📝 **標準的なデータ構造**

### 投手データ形式（変更禁止）
```python
{
    "player_id": int,
    "name": str,
    "team": str,
    "pitchHand": str,  # "L" or "R"
    "stats": {
        "era": float,
        "fip": float,
        "xfip": float,
        "whip": float,
        "k_bb_percent": float,
        "gb_percent": float,
        "fb_percent": float,
        "swstr_percent": float,
        "babip": float
    },
    "splits": {
        "vs_left": {"avg": float, "ops": float},
        "vs_right": {"avg": float, "ops": float}
    },
    "last_updated": str  # ISO format
}
```

### レポートヘッダー形式（変更禁止）
```
============================================================
MLB試合予想レポート - 日本時間 YYYY/MM/DD の試合
============================================================
[レベル] データ信頼性: ステータス (X/4データが本日更新) | HH:MM時点
------------------------------------------------------------
```

## 🎯 **コード生成時の注意事項**

### エラーハンドリング
```python
# 必ずこのパターンを使用
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
except requests.exceptions.Timeout:
    logger.error(f"Timeout accessing {url}")
    return None
except requests.exceptions.RequestException as e:
    logger.error(f"Error fetching data from {url}: {e}")
    return None
```

### ログ出力
```python
# 統一されたログフォーマット
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 命名規則
- クラス名: `PascalCase`
- 関数名: `snake_case`
- 定数: `UPPER_SNAKE_CASE`
- プライベート関数: `_snake_case`

## 🚨 **よくある問題と解決策**

### 1. データ更新が「0/4」と表示される
- 原因: データ更新チェック機能の不具合
- 解決: `core/data_freshness_checker.py`の実装を確認

### 2. 投手の利き腕が全て「右」
- 原因: キャッシュが古いまたは不完全
- 解決: `fetch_all_mlb_pitchers.py`を実行してキャッシュ更新

### 3. PDF生成エラー
- 原因: WeasyPrintの依存関係問題
- 解決: Chrome経由の手動保存を使用

## 📊 **API情報**

### MLB Stats API
- Base URL: `https://statsapi.mlb.com/api/v1/`
- 主要エンドポイント:
  - `/schedule` - 試合スケジュール
  - `/game/{game_id}/feed/live` - 試合詳細
  - `/people/{player_id}` - 選手情報
  - `/people/{player_id}/stats` - 選手統計

### FanGraphs（未実装）
- 現在はダミーデータ
- 今後実装予定

## ✅ **コード提供時のチェックリスト**

新しいコードを提供する際は、以下を確認してください：

- [ ] 既存コードとの整合性
- [ ] エラーハンドリングの実装
- [ ] ログ出力の追加
- [ ] データ構造の維持
- [ ] 命名規則の遵守
- [ ] 影響範囲の明記
- [ ] テスト方法の提示

## 📝 **標準的な回答フォーマット**

```markdown
## 確認事項
- 既存コードを確認しました: [ファイル名]
- 影響を受けるファイル: [リスト]

## 実装内容
[コード]

## 注意点
- [既存機能への影響]
- [必要な追加作業]

## テスト方法
[テストコマンド]
```

## 🔄 **更新履歴**

- 2025-08-25: 初版作成
- データ更新チェック機能の問題を確認中
- FanGraphs API統合待ち

---

**このプロジェクトでコードを生成する際は、必ず既存コードを確認してから作業してください。**