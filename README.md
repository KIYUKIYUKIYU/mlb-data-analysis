# 🏟️ MLB Data Analysis Project

[![Daily Report](https://github.com/KIYUKIYUKIYU/mlb-data-analysis/actions/workflows/daily_mlb_report.yml/badge.svg)](https://github.com/KIYUKIYUKIYU/mlb-data-analysis/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Last Updated](https://img.shields.io/badge/last%20updated-2025--08--25-green.svg)](https://github.com/KIYUKIYUKIYU/mlb-data-analysis)

MLB試合データを自動収集・分析し、日本時間19:30に予想レポートを生成するシステム

## 📋 目次

- [プロジェクト概要](#プロジェクト概要)
- [⚠️ 重要: 開発ルール](#️-重要-開発ルール)
- [システム構成](#システム構成)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [API/データソース](#apiデータソース)
- [トラブルシューティング](#トラブルシューティング)

## プロジェクト概要

### 🎯 主な機能
- **自動データ収集**: MLB Stats APIから試合・選手データを取得
- **統計分析**: ERA、FIP、xFIP、WHIP等の高度な指標を計算
- **レポート生成**: テキスト/HTML/PDF形式で出力
- **自動実行**: GitHub Actionsで毎日19:30（JST）に実行
- **Google Drive連携**: レポートを自動保存

### 📊 生成されるレポート内容
- 試合予想と分析
- 先発投手の詳細統計
- チーム打撃成績
- 中継ぎ陣の状態
- データ信頼性スコア（0/4〜4/4）

---

## ⚠️ **重要: 開発ルール**

### 🔴 **絶対的なルール: 既存コード確認の義務**

**新しいコードを生成または修正する前に、必ず以下を実行すること：**

```markdown
1. 既存コードの確認 [必須]
   - 関連するファイルのURLを提供
   - または関連コードを貼り付け
   
2. 影響範囲の特定 [必須]
   - 修正が影響する他のファイルをリストアップ
   - 依存関係を明確化
   
3. 整合性の確認 [必須]
   - 既存の命名規則に従う
   - 既存のデータ構造を維持
   - 既存のエラーハンドリングパターンを踏襲
```

### 📝 **AIアシスタント（Claude等）への指示テンプレート**

```markdown
## コード修正依頼

### 1. 確認してほしい既存コード
- メインファイル: https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/scripts/mlb_complete_report_real.py
- 関連ファイル: https://raw.githubusercontent.com/KIYUKIYUKIYU/mlb-data-analysis/main/src/mlb_api_client.py

### 2. 修正内容
[具体的な修正内容を記載]

### 3. 注意事項
- 既存コードとの整合性を保つこと
- 他のモジュールへの影響を考慮すること
- エラーハンドリングを適切に行うこと
```

### ✅ **開発チェックリスト**

新規開発・修正時は以下を確認：

- [ ] 既存コードを確認した
- [ ] 影響範囲を特定した
- [ ] 既存の命名規則に従っている
- [ ] エラーハンドリングを実装した
- [ ] ログ出力を適切に設定した
- [ ] キャッシュへの影響を確認した
- [ ] テストを実行した（ローカル）
- [ ] ドキュメントを更新した

---

## 🏗️ システム構成

### ディレクトリ構造
```
mlb-data-analysis/
├── .github/workflows/
│   └── daily_mlb_report.yml    # GitHub Actions設定（19:30 JST実行）
├── src/
│   └── mlb_api_client.py       # MLB Stats API クライアント
├── scripts/
│   ├── mlb_complete_report_real.py  # メインレポート生成
│   ├── convert_to_html.py          # HTML変換
│   ├── convert_to_pdf.py           # PDF変換
│   ├── fetch_all_mlb_pitchers.py   # 投手データ一括取得
│   └── upload_to_drive.py          # Google Drive アップロード
├── cache/
│   └── pitcher_info/            # 投手情報キャッシュ（JSON）
├── daily_reports/
│   ├── *.txt                    # テキストレポート
│   ├── html/*.html              # HTMLレポート
│   └── pdf/*.pdf                # PDFレポート
├── core/                        # コアモジュール（開発中）
│   └── data_freshness_checker.py   # データ更新チェック
├── requirements.txt             # 依存パッケージ
└── README.md                    # このファイル
```

### 主要ファイルの役割

| ファイル | 役割 | 依存関係 |
|---------|------|----------|
| `mlb_complete_report_real.py` | レポート生成のメインロジック | `mlb_api_client.py` |
| `mlb_api_client.py` | MLB APIとの通信 | なし |
| `convert_to_html.py` | テキスト→HTML変換 | なし |
| `convert_to_pdf.py` | HTML→PDF変換（Chrome経由） | なし |
| `fetch_all_mlb_pitchers.py` | 全投手データ取得・キャッシュ | `mlb_api_client.py` |

---

## 🚀 セットアップ

### 前提条件
- Python 3.10以上
- Git
- Google Chrome（PDF生成用）

### インストール手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/KIYUKIYUKIYU/mlb-data-analysis.git
cd mlb-data-analysis

# 2. 仮想環境を作成
python -m venv venv

# 3. 仮想環境を有効化
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. 依存パッケージをインストール
pip install -r requirements.txt

# 5. 投手データのキャッシュを作成
python scripts/fetch_all_mlb_pitchers.py
```

### 環境変数設定（Google Drive連携用）

```bash
# Google認証情報
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'
export GOOGLE_DRIVE_FOLDER_ID='1vL6tVcGclh7yLtBuKknZMn0cdsVloRph'
```

---

## 📖 使用方法

### 基本的な使用方法

```bash
# レポート生成
python scripts/mlb_complete_report_real.py

# HTML変換
python scripts/convert_to_html.py "daily_reports/MLB08月25日(月)レポート.txt"

# PDF変換（Chromeで開く）
python scripts/convert_to_pdf.py "daily_reports/html/MLB08月25日(月)レポート.html"
```

### 自動実行
GitHub Actionsにより毎日19:30（JST）に自動実行されます。

手動実行：
1. [Actions](https://github.com/KIYUKIYUKIYU/mlb-data-analysis/actions)ページへ
2. "Daily MLB Report"を選択
3. "Run workflow"をクリック

---

## 📊 API/データソース

### 1. MLB Stats API
- **エンドポイント**: `https://statsapi.mlb.com/api/v1/`
- **取得データ**: 
  - 試合スケジュール
  - 投手・打者統計
  - チーム成績
  - リアルタイム試合データ

### 2. FanGraphs（計画中）
- **取得予定データ**: FIP、xFIP、K-BB%、GB%、FB%
- **現状**: 実装待ち（現在はダミーデータ）

### 3. ローカルキャッシュ
- **場所**: `cache/pitcher_info/`
- **形式**: JSON
- **更新頻度**: 24時間

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. データ信頼性が「0/4」と表示される
```bash
# 投手キャッシュを更新
python scripts/fetch_all_mlb_pitchers.py

# データ更新状況を確認
python core/data_freshness_checker.py
```

#### 2. PDF変換でエラー
```bash
# Chromeで手動保存
python scripts/convert_to_pdf.py [HTMLファイル]
# メニューで「2」を選択 → Ctrl+P → PDFとして保存
```

#### 3. 文字化け
- ファイルエンコーディングをUTF-8に統一
- BOMなしで保存

#### 4. Google Drive連携エラー
- 事前にファイルを手動作成
- サービスアカウントに編集権限を付与

---

## 🤝 貢献方法

### コード修正の手順

1. **既存コードの確認**
   ```bash
   # 関連ファイルを確認
   cat scripts/mlb_complete_report_real.py
   cat src/mlb_api_client.py
   ```

2. **ブランチ作成**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **修正実施**
   - 既存コードとの整合性を保つ
   - エラーハンドリングを追加
   - ログを適切に出力

4. **テスト**
   ```bash
   python scripts/mlb_complete_report_real.py
   ```

5. **プルリクエスト**
   - 変更内容を明記
   - 影響範囲を説明
   - テスト結果を記載

---

## 📝 今後の計画

### 優先度: 高
- [ ] FanGraphs APIの実装
- [ ] データ更新チェック機能の改善
- [ ] エラーハンドリングの強化

### 優先度: 中
- [ ] NPBデータ統合
- [ ] モジュール化（core/models/services分離）
- [ ] 非同期処理の導入

### 優先度: 低
- [ ] Baseball Reference統合
- [ ] Statcastデータ追加
- [ ] 機械学習による予測モデル

---

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

---

## 👥 コントリビューター

- [@KIYUKIYUKIYU](https://github.com/KIYUKIYUKIYU) - プロジェクトオーナー

---

## 📞 お問い合わせ

問題や提案がある場合は、[Issues](https://github.com/KIYUKIYUKIYU/mlb-data-analysis/issues)でお知らせください。

---

## 🔗 関連リンク

- [MLB Stats API Documentation](https://statsapi.mlb.com/docs/)
- [FanGraphs](https://www.fangraphs.com/)
- [Baseball Reference](https://www.baseball-reference.com/)

---

**最終更新**: 2025年8月25日