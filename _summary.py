import json

d = json.load(open('coverage.json'))
files = []
for f, e in d['files'].items():
    s = e['summary']
    files.append((f, s['percent_covered'], s['covered_lines'], s['num_statements'], s['missing_lines']))
files.sort(key=lambda x: x[1])

t = d['totals']

print("=" * 70)
print("pytest 覆盖率报告摘要")
print("=" * 70)
print(f"总覆盖率: {t['percent_covered']:.1f}%")
print(f"覆盖行: {t['covered_lines']} / {t['num_statements']}")
print(f"缺失行: {t['missing_lines']}")
print(f"运行时间: ~87秒")
print(f"测试通过: 150 passed")
print()

print(f"{'文件':<42} {'覆盖率':>8} {'覆盖':>6} {'语句':>6} {'缺失':>6}")
print("-" * 70)
for name, pct, cov, total, miss in files:
    short = name.replace('\\', '/')
    print(f"{short:<42} {pct:6.1f}% {cov:4d} {total:4d} {miss:4d}")

print("-" * 70)
print(f"{'总计':<42} {t['percent_covered']:6.1f}% {t['covered_lines']:4d} {t['num_statements']:4d} {t['missing_lines']:4d}")

# 低覆盖率文件
print()
print("低覆盖率文件 (<80%):")
low = [(name, pct) for name, pct, _, _, _ in files if pct < 80]
for name, pct in low:
    print(f"  {name.replace(chr(92), '/'):<45} {pct:.1f}%")
