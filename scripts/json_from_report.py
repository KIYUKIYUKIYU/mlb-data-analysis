# scripts/json_from_report.py
# -*- coding: utf-8 -*-
"""
Create models/mlb_daily_YYYYMMDD.json by parsing an already-generated TXT report
(e.g., daily_reports/MLB2025-08-25.txt). This is a *pass-through* extractor:
- No recalculation
- If a value isn't present in the report, we omit the field (do not insert nulls)
- Multiple games supported per report
Usage:
    python scripts/json_from_report.py --date 2025-08-25 ^
        --report "daily_reports\MLB2025-08-25.txt" ^
        --out "models\mlb_daily_from_report_20250825.json"
"""
import argparse, json, os, re
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))

def to_float_safe(s: str):
    try:
        s = s.strip()
        if s.endswith('%'):
            return float(s[:-1])
        return float(s)
    except Exception:
        return None

def normalize_hand(hand_ja: str):
    if '右' in hand_ja: return 'R'
    if '左' in hand_ja: return 'L'
    if '両' in hand_ja: return 'S'
    return 'TBD'

def iso_local(date_str: str, hm: str):
    try:
        dt = datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M").replace(tzinfo=JST)
        return dt.isoformat()
    except Exception:
        return None

def iso_utc(date_str: str, hm: str):
    try:
        dt = datetime.strptime(f"{date_str} {hm}", "%Y-%m-%d %H:%M").replace(tzinfo=JST).astimezone(timezone.utc)
        return dt.isoformat()
    except Exception:
        return None

def guess_report_path(date_str: str):
    ymd = date_str.replace('-', '')
    p1 = os.path.join("daily_reports", f"MLB{date_str}.txt")
    if os.path.exists(p1): return p1
    candidates = []
    for base in ["daily_reports", "."]:
        if not os.path.isdir(base): continue
        for name in os.listdir(base):
            if name.endswith(".txt") and "MLB" in name and ymd[4:6] in name and ymd[6:8] in name:
                candidates.append(os.path.join(base, name))
    if candidates:
        candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return candidates[0]
    return None

def parse_report(text: str, date_str: str):
    lines = text.splitlines()
    games = []

    current = None
    team_ctx = None  # 'away' or 'home'

    re_matchup = re.compile(r'^([A-Za-z .\'-]+)\s+@\s+([A-Za-z .\'-]+)\s*$')
    re_start   = re.compile(r'^開始時刻:\s*(\d{2})/(\d{2})\s+(\d{2}):(\d{2})')
    re_team_header = re.compile(r'^【(.+?)】')
    re_starter = re.compile(r'^先発:\s*(.+?)\s*（(.+?)）\s*（(\d+)勝(\d+)敗）')
    re_metrics_line = re.compile(r'([A-Za-z%]+):\s*([0-9.]+%?)')
    re_vs_split = re.compile(r'対左.*?([0-9.]+)\s*\(OPS\s*([0-9.]+)\).*?対右.*?([0-9.]+)\s*\(OPS\s*([0-9.]+)\)')
    re_bullpen_head = re.compile(r'^中継ぎ陣\s*\((\d+)名\):')
    re_role_cl = re.compile(r'^CL:\s*(.+)$')
    re_role_su = re.compile(r'^SU:\s*(.+)$')
    re_fatigue = re.compile(r'^疲労度:\s*(.+)$')
    re_batting_head = re.compile(r'^チーム打撃:')
    re_last_ops = re.compile(r'過去5試合OPS:\s*([0-9.]+)\s*\|\s*過去10試合OPS:\s*([0-9.]+)')

    def ensure_game():
        nonlocal current
        if current is None:
            current = {
                "league": "MLB",
                "season": datetime.fromisoformat(date_str + "T00:00:00").year,
                "status": "NS",
                "start_time_local": None,
                "start_time_utc": None,
                "venue": None,
                "matchup": {},
                "starters": {"away": {}, "home": {}},
                "bullpens": {"away": {}, "home": {}},
                "batting": {"away": {}, "home": {}},
            }

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        m = re_matchup.match(line)
        if m:
            if current and current.get("matchup", {}).get("away_team"):
                games.append(current)
            current = None
            ensure_game()
            away, home = m.group(1), m.group(2)
            current["matchup"]["away_team"] = away
            current["matchup"]["home_team"] = home
            team_ctx = None
            i += 1
            continue

        m = re_start.match(line)
        if m and current is not None:
            _, _, HH, MM = m.groups()
            hm = f"{HH}:{MM}"
            current["start_time_local"] = iso_local(date_str, hm)
            current["start_time_utc"] = iso_utc(date_str, hm)
            i += 1
            continue

        m = re_team_header.match(line)
        if m and current is not None:
            team_name = m.group(1).strip()
            if team_name == current["matchup"].get("away_team"):
                team_ctx = "away"
            elif team_name == current["matchup"].get("home_team"):
                team_ctx = "home"
            else:
                team_ctx = "away" if not current["starters"]["away"] else "home"
            i += 1
            continue

        m = re_starter.match(line)
        if m and current is not None and team_ctx:
            name, hand_ja, w, l = m.groups()
            starter = {"name": name.strip(), "hand": normalize_hand(hand_ja), "probable": True}
            try:
                starter["season"] = {"w": int(w), "l": int(l)}
            except Exception:
                pass
            current["starters"][team_ctx] = starter
            i += 1
            continue

        if '|' in line and any(k in line for k in ['ERA', 'FIP', 'xFIP', 'WHIP', 'K-BB%', 'GB%', 'FB%', 'QS', 'SwStr', 'BABIP']):
            parts = [p.strip() for p in line.split('|')]
            metrics = {}
            for p in parts:
                mm = re_metrics_line.findall(p.replace('％', '%').replace('率', ''))
                for key, val in mm:
                    key = key.replace('SwStr', 'SwStr%').replace('K-BB', 'K-BB%')
                    kmap = {
                        'ERA':'era','FIP':'fip','xFIP':'xfip','WHIP':'whip',
                        'K-BB%':'kbb_pct','GB%':'gb_pct','FB%':'fb_pct',
                        'QS':'qs_pct','QS%':'qs_pct','SwStr%':'swstr_pct','BABIP':'babip'
                    }
                    if key in kmap:
                        fv = to_float_safe(val)
                        if fv is not None:
                            metrics[kmap[key]] = fv
            target = None
            if team_ctx and current["starters"].get(team_ctx):
                target = current["starters"][team_ctx].setdefault("season", {})
            elif team_ctx:
                target = current["bullpens"][team_ctx]
            if target is not None:
                target.update(metrics)
            i += 1
            continue

        m = re_vs_split.search(line)
        if m and team_ctx and current is not None:
            l_avg, l_ops, r_avg, r_ops = m.groups()
            dest = None
            if current["starters"].get(team_ctx):
                dest = current["starters"][team_ctx].setdefault("splits", {})
            else:
                dest = current["batting"][team_ctx].setdefault("vs_hand", {})
            dest["vs_lhp"] = {"avg": to_float_safe(l_avg), "ops": to_float_safe(l_ops)}
            dest["vs_rhp"] = {"avg": to_float_safe(r_avg), "ops": to_float_safe(r_ops)}
            i += 1
            continue

        m = re_bullpen_head.match(line)
        if m and team_ctx and current is not None:
            count = int(m.group(1))
            current["bullpens"][team_ctx]["count"] = count
            i += 1
            continue

        m = re_role_cl.match(line)
        if m and team_ctx and current is not None:
            current["bullpens"][team_ctx]["cl"] = m.group(1).strip()
            i += 1
            continue
        m = re_role_su.match(line)
        if m and team_ctx and current is not None:
            current["bullpens"][team_ctx]["su"] = m.group(1).strip()
            i += 1
            continue

        m = re_fatigue.match(line)
        if m and team_ctx and current is not None:
            current["bullpens"][team_ctx]["fatigue_note"] = m.group(1).strip()
            i += 1
            continue

        m = re_batting_head.match(line)
        if m and team_ctx and current is not None:
            i += 1
            while i < len(lines):
                l2 = lines[i].strip()
                if not l2 or l2.startswith('【') or l2.startswith('中継ぎ陣') or l2.startswith('====') or re_matchup.match(l2):
                    break
                parts = [p.strip() for p in l2.split('|') if p.strip()]
                for p in parts:
                    if ':' in p:
                        key, val = [x.strip() for x in p.split(':', 1)]
                        key_en = {
                            'AVG':'avg', 'OPS':'ops', '得点':'runs', '本塁打':'hr',
                            'wOBA':'woba', 'xwOBA':'xwoba', 'Barrel%':'barrel_pct', 'Hard-Hit%':'hardhit_pct'
                        }.get(key, None)
                        if key_en:
                            fv = to_float_safe(val)
                            if fv is not None:
                                current["batting"][team_ctx].setdefault("season", {})[key_en] = fv
                        mlast = re_last_ops.search(l2)
                        if mlast:
                            g5, g10 = mlast.groups()
                            if g5: current["batting"][team_ctx].setdefault("last_5_games", {})["ops"] = to_float_safe(g5)
                            if g10: current["batting"][team_ctx].setdefault("last_10_games", {})["ops"] = to_float_safe(g10)
                i += 1
            continue

        i += 1

    if current and current.get("matchup", {}).get("away_team"):
        games.append(current)

    return games

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (JST)")
    ap.add_argument("--report", default=None, help="Path to TXT report")
    ap.add_argument("--out", default=None, help="Output JSON path (default: models/mlb_daily_from_report_YYYYMMDD.json)")
    args = ap.parse_args()

    date_str = args.date
    report_path = args.report or guess_report_path(date_str)
    if not report_path or not os.path.exists(report_path):
        raise SystemExit(f"[error] report not found. Try --report. looked for: {report_path}")

    with open(report_path, "r", encoding="utf-8") as f:
        text = f.read()

    games = parse_report(text, date_str)

    out = {
        "generated_at": datetime.now(JST).isoformat(),
        "date": date_str,
        "timezone": "Asia/Tokyo",
        "games_count": len(games),
        "source_meta": {
            "report_path": report_path,
            "strategy": "pass-through-from-report"
        },
        "games": games
    }

    os.makedirs("models", exist_ok=True)
    default_out = os.path.join("models", f"mlb_daily_from_report_{date_str.replace('-','')}.json")
    out_path = args.out or default_out
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"✅ saved: {out_path} (games: {len(games)})")

if __name__ == "__main__":
    main()
