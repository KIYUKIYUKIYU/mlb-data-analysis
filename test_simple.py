import sys
import os

print("Python Path:")
for p in sys.path:
    print(f"  {p}")

print("\\nChecking files:")
files_to_check = [
    "src/mlb_api_client.py",
    "scripts/enhanced_stats_collector.py",
    "scripts/bullpen_enhanced_stats.py",
    "scripts/batting_quality_stats.py"
]

for f in files_to_check:
    if os.path.exists(f):
        print(f"✓ {f} exists")
    else:
        print(f"✗ {f} NOT FOUND")

print("\\nTrying imports:")
try:
    from src.mlb_api_client import MLBApiClient
    print("✓ MLBApiClient imported")
except Exception as e:
    print(f"✗ MLBApiClient error: {e}")