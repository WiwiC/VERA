import pandas as pd
import sys

def analyze_report(file_path):
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None

    total = len(df)
    if total == 0:
        return None

    exact = (df['bucket_distance'] == 0).sum()
    off1 = (df['bucket_distance'] == 1).sum()
    acceptable = exact + off1

    metrics = df.groupby('metric').apply(lambda x: (x['bucket_distance'] == 0).mean() * 100).sort_values(ascending=False)

    return {
        'total': total,
        'exact': exact,
        'off1': off1,
        'acceptable': acceptable,
        'exact_pct': exact / total * 100,
        'off1_pct': off1 / total * 100,
        'acceptable_pct': acceptable / total * 100,
        'metrics': metrics
    }

new_report_path = 'data/calibration_report_20251211_142837.csv'
old_report_path = 'data/calibration_report_20251211_112829.csv'

new_stats = analyze_report(new_report_path)
old_stats = analyze_report(old_report_path)

if not new_stats or not old_stats:
    sys.exit(1)

print('Summary of Results:')
print(f'Exact Matches: {new_stats["exact_pct"]:.1f}% ({new_stats["exact"]}/{new_stats["total"]})')
print(f'Close Matches (Off by 1): {new_stats["off1_pct"]:.1f}% ({new_stats["off1"]}/{new_stats["total"]})')
print(f'Total Acceptable (<=1 label step away): {new_stats["acceptable_pct"]:.1f}%')
print('Top Performing Metrics:')
for m, acc in new_stats['metrics'].head(5).items():
    print(f'  - {m}: {acc:.1f}%')

print('\n--- COMPARISON (New vs Old) ---')
diff_exact = new_stats["exact_pct"] - old_stats["exact_pct"]
diff_accept = new_stats["acceptable_pct"] - old_stats["acceptable_pct"]
print(f'Overall Accuracy: {new_stats["exact_pct"]:.1f}% vs {old_stats["exact_pct"]:.1f}% (Diff: {diff_exact:+.1f}%)')
print(f'Total Acceptable: {new_stats["acceptable_pct"]:.1f}% vs {old_stats["acceptable_pct"]:.1f}% (Diff: {diff_accept:+.1f}%)')

print('\n--- Metric Improvements ---')
for m in new_stats['metrics'].index:
    new_acc = new_stats['metrics'][m]
    old_acc = old_stats['metrics'].get(m, 0)
    diff = new_acc - old_acc
    print(f'{m}: {new_acc:.1f}% (was {old_acc:.1f}%) -> {diff:+.1f}%')
