"""
生成论文所需的描述统计表（LaTeX 格式）。
对关键连续变量和二元变量计算基本统计量，输出为 .tex 文件供 paper.tex 引用。
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from utils import load_data, print_section, TABLES_DIR

print_section("生成描述统计表")

df = load_data()

# ── 轻量清洗 ──
for col in ["livingRoom", "drawingRoom", "bathRoom", "constructionTime", "DOM"]:
    if col in df.columns and df[col].dtype == object:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df = df[df["price"] > 100].copy()
df["log_price"] = np.log(df["price"])

# 计算距市中心距离（度）
center_lng, center_lat = 116.397, 39.909  # 天安门
df["dist_center"] = np.sqrt((df["Lng"] - center_lng)**2 + (df["Lat"] - center_lat)**2)

# ladderRatio 1% 截尾，避免极端值扭曲均值/标准差
for col in ["ladderRatio"]:
    if col in df.columns:
        lo, hi = df[col].quantile(0.01), df[col].quantile(0.99)
        df[col] = df[col].clip(lo, hi)

print(f"清洗后样本量：{len(df):,}")

# ── 定义需要展示的变量 ──
cont_vars = {
    "price": "单价（元/m$^2$）",
    "log_price": "对数单价",
    "dist_center": "距市中心距离（度）",
    "square": "建筑面积（m$^2$）",
    "Lng": "经度",
    "Lat": "纬度",
    "ladderRatio": "梯户比",
    "DOM": "挂牌天数",
    "constructionTime": "建造年份",
}

binary_vars = {
    "elevator": "有电梯",
    "subway": "临近地铁",
    "fiveYearsProperty": "满五年",
}

# ── 计算连续变量统计 ──
rows = []
for var, label in cont_vars.items():
    if var not in df.columns:
        continue
    s = df[var].dropna()
    rows.append({
        "变量": label,
        "均值": f"{s.mean():,.1f}",
        "标准差": f"{s.std():,.1f}",
        "最小值": f"{s.min():,.1f}",
        "中位数": f"{s.median():,.1f}",
        "最大值": f"{s.max():,.1f}",
    })

# ── 计算二元变量统计（显示比例） ──
for var, label in binary_vars.items():
    if var not in df.columns:
        continue
    s = df[var].dropna()
    prop = s.mean()
    rows.append({
        "变量": f"{label}（比例）",
        "均值": f"{prop:.3f}",
        "标准差": f"{np.sqrt(prop*(1-prop)):.3f}",
        "最小值": "0",
        "中位数": f"{int(s.median())}",
        "最大值": "1",
    })

stats_df = pd.DataFrame(rows)
print(stats_df.to_string(index=False))

# ── 生成 LaTeX 表格 ──
latex_lines = []
latex_lines.append(r"\begin{table}[H]")
latex_lines.append(r"\centering")
latex_lines.append(r"\caption{关键变量描述统计}")
latex_lines.append(r"\label{tab:descriptive_stats}")
latex_lines.append(r"\begin{tabular}{lrrrrr}")
latex_lines.append(r"\toprule")
latex_lines.append(r"变量 & 均值 & 标准差 & 最小值 & 中位数 & 最大值 \\")
latex_lines.append(r"\midrule")

for _, row in stats_df.iterrows():
    latex_lines.append(
        f"{row['变量']} & {row['均值']} & {row['标准差']} & {row['最小值']} & {row['中位数']} & {row['最大值']} \\\\"
    )

latex_lines.append(r"\bottomrule")
latex_lines.append(r"\end{tabular}")
latex_lines.append(r"\end{table}")

table_tex = "\n".join(latex_lines)

# 保存
out_path = TABLES_DIR / "descriptive_stats_latex.tex"
with open(out_path, "w", encoding="utf-8") as f:
    f.write(table_tex)
print(f"\nLaTeX 表格已保存至：{out_path}")

# ── 关键统计量摘要 ──
print(f"\n样本量：{len(df):,}")
print(f"变量数：{len(df.columns)}")
print(f"价格均值：{df['price'].mean():,.1f}")
print(f"对数价格均值：{df['log_price'].mean():.4f}，偏度：{df['log_price'].skew():.3f}")
print(f"电梯比例：{df['elevator'].mean():.3f}")
print(f"地铁比例：{df['subway'].mean():.3f}")
print(f"满五年比例：{df['fiveYearsProperty'].mean():.3f}")
