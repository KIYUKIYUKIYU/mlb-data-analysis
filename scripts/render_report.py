# scripts/render_report.py
# -*- coding: utf-8 -*-
"""
共通データモデル(JSON)を読み込み、Jinja2テンプレでTXT/HTMLを描画
使い方:
  python scripts\render_report.py --date 2025-08-25 --template templates\mlb_daily.txt.j2 --out daily_reports\MLB2025-08-25.txt
"""
import argparse, json
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--date", required=True, help="YYYY-MM-DD")
    p.add_argument("--model", help="モデルJSON（省略時: models/mlb_daily_YYYYMMDD.json）")
    p.add_argument("--template", required=True, help="templates\\*.j2")
    p.add_argument("--out", required=True, help="出力パス .txt/.html")
    return p.parse_args()

def ymd(s: str) -> str:
    return datetime.strptime(s, "%Y-%m-%d").strftime("%Y%m%d")

def main():
    args = parse_args()
    model_path = Path(args.model) if args.model else Path(f"models/mlb_daily_{ymd(args.date)}.json")
    if not model_path.exists():
        raise FileNotFoundError(f"モデルが見つかりません: {model_path}")
    data = json.loads(model_path.read_text(encoding="utf-8"))

    tpl_path = Path(args.template)
    env = Environment(
        loader=FileSystemLoader(str(tpl_path.parent)),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html",))
    )
    template = env.get_template(tpl_path.name)
    rendered = template.render(model=data)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"[render_report] ✅ written: {out.resolve()}")

if __name__ == "__main__":
    main()
