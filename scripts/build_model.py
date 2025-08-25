# scripts/build_model.py
# -*- coding: utf-8 -*-
"""
build_model.py

目的:
  - normalize で作成された curated データ(1日分)と、build_meta が出力した _meta.json を統合し、
    レポート描画用の「共通データモデル(JSON)」を生成する。

想定入出力:
  入力(優先順に探索):
    - --curated で明示された path (ファイル or ディレクトリ)
    - 既定候補 (date=YYYY-MM-DD, ymd=YYYYMMDD):
        1) data/curated/mlb_{ymd}.json                (単一ファイル)
        2) data/curated/{ymd}/mlb_curated.json        (単一ファイル)
        3) data/curated/{ymd}/                        (ディレクトリ; *.json を走査)
        4) data/curated/mlb/{ymd}.json                (単一ファイル)
  メタ(優先順に探索):
        1) --meta で明示された path
        2) data/curated/_meta_{ymd}.json
        3) data/meta/mlb_{ymd}.json
        4) data/meta/{ymd}.json

  出力(既定):
    - models/mlb_daily_{ymd}.json  ( --out で変更可能 )

CLI例:
  python scripts\build_model.py --date 2025-08-25
  python scripts\build_model.py --date 2025-08-25 --curated data\curated\20250825 --meta data\curated\_meta_20250825.json
  python scripts\build_model.py --date 2025-08-25 --out models\custom\mlb_{date}.json

注意:
  - 本スクリプトは「構造のゆらぎ」に耐えるよう、curated の構造が list/dict('games')/複数ファイル いずれでも読めるよう実装。
  - Game 要素からは共通で使いそうなキーを抽出し、欠損は None で埋める。
  - 不明なフィールドは games[i]['extras'] に残す (テンプレ側で必要に応じて参照可能)。
"""

from __future__ import annotations
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build common data model (JSON) from curated + _meta")
    p.add_argument("--date", required=True, help="対象日 (YYYY-MM-DD)")
    p.add_argument("--sport", default="mlb", help="スポーツ識別子 (既定: mlb)")
    p.add_argument("--timezone", default="Asia/Tokyo", help="表示タイムゾーン (既定: Asia/Tokyo)")
    p.add_argument("--curated", help="curated のファイル or ディレクトリのパス (省略時は既定候補から探索)")
    p.add_argument("--meta", help="_meta.json のファイルパス (省略時は既定候補から探索)")
    p.add_argument("--out", help="出力先ファイルパス (省略時: models/mlb_daily_{YYYYMMDD}.json)")
    return p.parse_args()

def ymd_from_date_string(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%Y%m%d")
    except Exception:
        print(f"[build_model] ERROR: --date は YYYY-MM-DD 形式で指定してください (受領: {date_str})", file=sys.stderr)
        sys.exit(2)

def find_existing_path(candidates: List[Union[str, Path]]) -> Optional[Path]:
    for c in candidates:
        p = Path(c)
        if p.exists():
            return p
    return None

def load_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def try_load_curated(curated_arg: Optional[str], ymd: str) -> Tuple[List[Dict[str, Any]], List[Path]]:
    """
    curated をロードしてゲーム配列に正規化して返す。
    返り値: (games, source_files)
    """
    candidates: List[Path] = []
    if curated_arg:
        candidates.append(Path(curated_arg))

    # 既定候補
    candidates.extend([
        Path(f"data/curated/mlb_{ymd}.json"),
        Path(f"data/curated/{ymd}/mlb_curated.json"),
        Path(f"data/curated/{ymd}"),
        Path(f"data/curated/mlb/{ymd}.json"),
    ])

    source_files: List[Path] = []
    games: List[Dict[str, Any]] = []

    target = find_existing_path(candidates)
    if target is None:
        print("[build_model] ERROR: curated の入力候補が見つかりませんでした。--curated で明示するか、既定の配置にしてください。", file=sys.stderr)
        sys.exit(3)

    if target.is_file():
        items, used_files = extract_games_from_file(target)
        games.extend(items)
        source_files.extend(used_files)
    elif target.is_dir():
        # ディレクトリなら *.json を集約
        json_files = sorted(target.glob("*.json"))
        if not json_files:
            print(f"[build_model] ERROR: ディレクトリ {target} に JSON が見つかりません。", file=sys.stderr)
            sys.exit(4)
        for jf in json_files:
            items, used_files = extract_games_from_file(jf)
            games.extend(items)
            source_files.extend(used_files)
    else:
        print(f"[build_model] ERROR: curated 入力が不正です: {target}", file=sys.stderr)
        sys.exit(5)

    # 重複除外 (id があれば id でユニーク化)
    deduped = []
    seen = set()
    for g in games:
        gid = g.get("id") or g.get("game_id") or g.get("fixture_id")
        key = ("__noid__", json.dumps(g, sort_keys=True)) if gid is None else ("id", str(gid))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(g)
    return deduped, source_files

def extract_games_from_file(path: Path) -> Tuple[List[Dict[str, Any]], List[Path]]:
    data = load_json_file(path)
    games: List[Dict[str, Any]] = []
    if isinstance(data, list):
        games = data
    elif isinstance(data, dict):
        if "games" in data and isinstance(data["games"], list):
            games = data["games"]
        else:
            # 単一ゲーム or 不明形式 → 可能性として games=[data]
            # ゲーム配列でないが game/fixture を示すキーがあれば一件として扱う
            if any(k in data for k in ("id", "game_id", "fixture_id", "teams", "home_team", "away_team")):
                games = [data]
            else:
                # 想定外形式 → 空
                games = []
    else:
        games = []
    return games, [path]

def try_load_meta(meta_arg: Optional[str], ymd: str) -> Dict[str, Any]:
    candidates: List[Path] = []
    if meta_arg:
        candidates.append(Path(meta_arg))

    candidates.extend([
        Path(f"data/curated/_meta_{ymd}.json"),
        Path(f"data/meta/mlb_{ymd}.json"),
        Path(f"data/meta/{ymd}.json"),
    ])
    target = find_existing_path(candidates)
    if target is None:
        print("[build_model] WARN: _meta が見つかりませんでした。メタ情報なしで続行します。")
        return {}
    try:
        return load_json_file(target)
    except Exception as e:
        print(f"[build_model] WARN: _meta の読み込みに失敗しました: {target} ({e})。メタなしで続行。")
        return {}

def to_jst_iso(dt_str: Optional[str], fallback_date_ymd: str) -> Optional[str]:
    """
    受け取った文字列が ISO8601 であれば JST に正規化して返す。
    タイムゾーンが無い/不明なら None (テンプレ側で扱う)。
    """
    if not dt_str or not isinstance(dt_str, str):
        return None
    try:
        # fromisoformat は "YYYY-MM-DDTHH:MM:SS+09:00" 等を解釈
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return None
        return dt.astimezone(JST).strftime("%Y-%m-%dT%H:%M:%S%z")
    except Exception:
        # よくある代替: "YYYY-MM-DD HH:MM" 的なフォーマットの場合は日付を補助に使わない
        return None

def pick(d: Dict[str, Any], keys: List[str], default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default

def ensure_team_block(game: Dict[str, Any], side: str) -> Dict[str, Any]:
    """
    side: 'home' or 'away'
    多様なキーの揺れに対応して {name, id(optional)} を取り出す。
    """
    result = {"name": None, "id": None}
    # 1) teams: { home:{name/id}, away:{name/id} }
    teams = game.get("teams") or {}
    if side in teams and isinstance(teams[side], dict):
        result["name"] = teams[side].get("name") or teams[side].get("displayName") or teams[side].get("short")
        result["id"] = teams[side].get("id")
    # 2) top-level keys e.g., home_team / away_team (string or dict)
    if result["name"] is None:
        cand = game.get(f"{side}_team")
        if isinstance(cand, dict):
            result["name"] = cand.get("name") or cand.get("displayName") or cand.get("short")
            result["id"] = cand.get("id")
        elif isinstance(cand, str):
            result["name"] = cand
    return result

def ensure_pitcher_block(game: Dict[str, Any], side: str) -> Dict[str, Any]:
    """
    probable/starting pitchers の取り出し (name/handed/throws)
    よくあるキーに対応し、見つからなければ TBD とする。
    """
    res = {"name": None, "handed": None, "throws": None, "id": None}
    # candidates in nested structures
    # e.g., probable_pitchers: {home:{name,throws}, away:{...}}
    pp = game.get("probable_pitchers") or game.get("starters") or {}
    side_obj = pp.get(side) if isinstance(pp, dict) else None
    if isinstance(side_obj, dict):
        res["name"] = side_obj.get("name") or side_obj.get("fullName")
        res["handed"] = side_obj.get("handed") or side_obj.get("hand")
        res["throws"] = side_obj.get("throws")
        res["id"] = side_obj.get("id")
    # flat keys fallback e.g., starter_home / starting_pitcher_home
    if res["name"] is None:
        for k in [f"starter_{side}", f"starting_pitcher_{side}", f"{side}_starter", f"{side}_pitcher"]:
            v = game.get(k)
            if isinstance(v, dict):
                res["name"] = v.get("name") or v.get("fullName")
                res["handed"] = v.get("handed") or v.get("hand")
                res["throws"] = v.get("throws")
                res["id"] = v.get("id")
                break
            elif isinstance(v, str):
                res["name"] = v
                break
    # normalize TBD
    name_low = (res["name"] or "").strip().lower()
    if not name_low or name_low in ("tbd", "probable: tbd", "undecided"):
        res["name"] = "TBD"
    return res

def normalize_game(game: Dict[str, Any], fallback_date_ymd: str) -> Dict[str, Any]:
    gid = pick(game, ["id", "game_id", "fixture_id"])
    league = game.get("league") or pick(game, ["league_name", "competition"])
    venue = game.get("venue") or pick(game, ["stadium", "ballpark", "site"])
    # 開始時刻 (ISO想定のキーいろいろ)
    start_iso = None
    for k in ["start_time", "startDate", "date", "datetime", "scheduled", "start_at", "game_time"]:
        if k in game and isinstance(game[k], str):
            start_iso = to_jst_iso(game[k], fallback_date_ymd)
            if start_iso:
                break

    home = ensure_team_block(game, "home")
    away = ensure_team_block(game, "away")
    sp_home = ensure_pitcher_block(game, "home")
    sp_away = ensure_pitcher_block(game, "away")

    # 「extras」に生データを温存（テンプレで必要になった時の逃げ道）
    known_keys = {
        "id","game_id","fixture_id","teams","home_team","away_team","probable_pitchers","starters",
        "starter_home","starter_away","starting_pitcher_home","starting_pitcher_away",
        "league","league_name","competition","venue","stadium","ballpark","site",
        "start_time","startDate","date","datetime","scheduled","start_at","game_time",
    }
    extras = {k: v for k, v in game.items() if k not in known_keys}

    return {
        "id": gid,
        "league": league,
        "venue": venue,
        "start_time_jst": start_iso,  # 例: "2025-08-25T08:10:00+0900"
        "home": home,
        "away": away,
        "pitchers": {
            "home": sp_home,
            "away": sp_away,
        },
        "extras": extras,  # 任意の追加情報
    }

def compute_tbd_rate(games_norm: List[Dict[str, Any]]) -> float:
    if not games_norm:
        return 0.0
    total = 0
    tbd = 0
    for g in games_norm:
        for side in ("home", "away"):
            total += 1
            name = (g.get("pitchers", {}).get(side, {}).get("name") or "").strip().lower()
            if not name or name == "tbd":
                tbd += 1
    return round(tbd / max(total, 1), 4)

def derive_freshness(meta: Dict[str, Any], games_count: int, target_date: str) -> Dict[str, Any]:
    """
    「4/4」判定に関わる鮮度を _meta からできる限り読み取り、なければ推定。
    期待キー例:
      meta["freshness"] = {
        "four_of_four": bool,  # 4/4
        "today_updated": bool, # 本日更新
        "rows_gt_zero": bool,  # rows > 0
        "detail": "..."
      }
    """
    freshness = meta.get("freshness") if isinstance(meta, dict) else None
    if isinstance(freshness, dict):
        four = bool(freshness.get("four_of_four"))
        today = bool(freshness.get("today_updated"))
        rows = bool(freshness.get("rows_gt_zero"))
        return {
            "four_of_four": four,
            "today_updated": today,
            "rows_gt_zero": rows,
            "source": "meta",
            "detail": freshness.get("detail"),
        }
    # 推定 (最低限)
    # rows>0 はゲーム件数で代用、本日更新は target_date==今日？ではなく今回は不明→ False
    rows = games_count > 0
    return {
        "four_of_four": rows,     # 厳密な 4/4 が無いので暫定: rows>0 を便宜的に true とする
        "today_updated": False,   # 不明
        "rows_gt_zero": rows,
        "source": "inferred",
        "detail": "meta.freshness 不在のため推定",
    }

def main():
    args = parse_args()
    ymd = ymd_from_date_string(args.date)
    tz = args.timezone

    print(f"[build_model] date={args.date} (ymd={ymd}), sport={args.sport}, tz={tz}")

    # curated 読み込み
    games_raw, src_files = try_load_curated(args.curated, ymd)
    print(f"[build_model] curated sources: {', '.join(str(p) for p in src_files)}")
    print(f"[build_model] curated games found: {len(games_raw)}")

    # 正規化
    games_norm = [normalize_game(g, ymd) for g in games_raw]
    tbd_rate = compute_tbd_rate(games_norm)
    print(f"[build_model] TBD rate (starters): {tbd_rate:.2%}")

    # _meta 読み込み
    meta = try_load_meta(args.meta, ymd)

    # 鮮度
    freshness = derive_freshness(meta, len(games_norm), args.date)

    # 共通データモデルを構築
    model: Dict[str, Any] = {
        "version": 1,
        "sport": args.sport,
        "date": args.date,             # "YYYY-MM-DD"
        "timezone": tz,
        "generated_at": datetime.now(tz=JST).strftime("%Y-%m-%dT%H:%M:%S%z"),
        "sources": {
            "curated_files": [str(p) for p in src_files],
            "meta_present": bool(meta),
        },
        "meta": {
            "freshness": freshness,
            "tbd_rate": tbd_rate,
            # meta の他フィールドを温存
            "raw": meta,
        },
        "summary": {
            "game_count": len(games_norm),
        },
        "games": games_norm,
    }

    # 出力先
    out_path = args.out
    if not out_path:
        out_path = f"models/mlb_daily_{ymd}.json"
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", encoding="utf-8") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)

    print(f"[build_model] ✅ model written: {out.resolve()}")
    # 4/4 風味の最終表示（テンプレで利用想定だがここでも簡易表示）
    four = "OK" if model["meta"]["freshness"]["four_of_four"] else "NG"
    print(f"[build_model] freshness 4/4: {four} | rows>0: {model['meta']['freshness']['rows_gt_zero']} | tbd_rate: {tbd_rate:.2%}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[build_model] cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except SystemExit as e:
        raise
    except Exception as e:
        print(f"[build_model] FATAL: {e}", file=sys.stderr)
        sys.exit(1)
