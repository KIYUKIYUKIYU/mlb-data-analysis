from scripts.batting_quality_stats import BattingQualityStats

# テスト実行
bs = BattingQualityStats()

# Yankees
print("Testing Yankees (147):")
stats = bs.get_team_quality_stats(147)
print(f"Result: {stats}")

# Orioles  
print("\nTesting Orioles (110):")
stats = bs.get_team_quality_stats(110)
print(f"Result: {stats}")