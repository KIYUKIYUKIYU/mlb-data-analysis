import glob, json, os

required_keys = ["RISP", "BABIP", "LOB", "HR/FB"]

files = glob.glob(r"data/pitcher_details/pitchers_detail_*.json")
if not files:
    print("[ERROR] JSONファイルが見つかりません")
    exit()

for f in files:
    with open(f, encoding="utf-8") as fp:
        try:
            data = json.load(fp)
        except json.JSONDecodeError:
            print(f"[INVALID JSON] {f}")
            continue
    if not isinstance(data, list):
        print(f"[SKIP] {f}: top-levelがlistではありません")
        continue

    print(f"\n=== {os.path.basename(f)} ===")
    for p in data:
        name = p.get("name") or p.get("名前") or "??"
        missing = [k for k in required_keys if k not in p or p[k] in (None, "", "-", 0)]
        if missing:
            print(f"  MISSING {name}: {', '.join(missing)}")
        else:
            print(f"  OK: {name}")
