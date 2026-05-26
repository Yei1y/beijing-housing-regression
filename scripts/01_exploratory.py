"""
脚本 1：探索性数据分析（EDA）
==============================
目标：了解数据结构、分布特征和基本关系。
为论文生成描述性图表和表格。

注意：原始数据存在已知质量问题：
  - 'livingRoom': 32 条为 '#NAME?'（Excel 损坏）
  - 'drawingRoom': 部分条目混入了楼层文本
  - 'bathRoom': 2 条为中文"未知"
  - 'constructionTime': 约 1.9 万条为"未知"
  - 'DOM': 50% 缺失
  - 'price': 部分极端/错误值（最小为 1）
  - 'ladderRatio': 2 个异常值超过 1000 万
这些问题在本脚本中仅做兼容处理，正式清洗在脚本 2 中完成。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import probplot
from utils import (
    setup_font, load_data, print_section, save_fig, save_table,
    CB_PALETTE, DIVERGING_CMAP, SEQUENTIAL_CMAP,
)

setup_font()


# ── 辅助函数 ──

def safe_numeric(series):
    """将序列强制转为数值，#NAME?/未知 等变为 NaN。"""
    return pd.to_numeric(series, errors="coerce")


def clean_for_eda(df):
    """轻量清洗，确保 EDA 绘图不会因脏数据崩溃。"""
    df = df.copy()
    # 本应是数值但可能混入文本的列
    for col in ["livingRoom", "drawingRoom", "bathRoom", "constructionTime"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = safe_numeric(df[col])
    if "DOM" in df.columns:
        df["DOM"] = safe_numeric(df["DOM"])
    # 过滤极端价格
    df = df[df["price"] > 100].copy()
    return df


# ── 1. 加载数据 ──
print_section("1. 加载数据")
raw = load_data()
df = clean_for_eda(raw)
print(f"价格过滤（>100）后：{len(df):,} 行（剔除 {len(raw) - len(df)} 条）")
print(f"内存占用：{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")

# ── 2. 基本信息 ──
print_section("2. 基本信息")
print(f"形状：{df.shape}")
print(f"\n列类型：")
print(df.dtypes.to_string())
missing = df.isnull().sum()
missing_pct = missing / len(df) * 100
missing_info = pd.DataFrame({"缺失数": missing, "占比(%)": missing_pct})
print(f"\n缺失值：")
print(missing_info[missing_info["缺失数"] > 0].to_string())

# ── 3. 描述性统计 ──
print_section("3. 描述性统计")
desc = df.describe(include="all").T
print(desc.to_string())
save_table(desc.reset_index().rename(columns={"index": "Variable"}), "descriptive_stats.csv")

# ── 4. 目标变量：价格 ──
print_section("4. 目标变量：每平米价格")

log_price = np.log(df["price"])

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

axes[0, 0].hist(df["price"], bins=80, color=CB_PALETTE[0], edgecolor="white", alpha=0.8)
axes[0, 0].set_xlabel("单价（元/㎡）")
axes[0, 0].set_ylabel("频数")
axes[0, 0].set_title("单价分布")

axes[0, 1].boxplot(df["price"], vert=False, patch_artist=True,
                    boxprops=dict(facecolor=CB_PALETTE[0], alpha=0.6))
axes[0, 1].set_xlabel("单价（元/㎡）")
axes[0, 1].set_title("单价箱线图")

axes[1, 0].hist(log_price, bins=80, color=CB_PALETTE[1], edgecolor="white", alpha=0.8)
axes[1, 0].set_xlabel("log(单价)")
axes[1, 0].set_ylabel("频数")
axes[1, 0].set_title("对数价格分布")

probplot(log_price, dist="norm", plot=axes[1, 1])
axes[1, 1].set_title("对数价格 Q-Q 图")
axes[1, 1].get_lines()[0].set_markerfacecolor(CB_PALETTE[0])
axes[1, 1].get_lines()[0].set_markersize(2)

save_fig("price_distribution.png", "01_eda")

print(f"价格均值：{df['price'].mean():.1f}，中位数：{df['price'].median():.1f}，"
      f"偏度：{df['price'].skew():.2f}，范围：[{df['price'].min()}, {df['price'].max()}]")
print(f"对数价格偏度：{log_price.skew():.2f}")

# ── 5. 相关分析 ──
print_section("5. 相关分析")

numeric_cols = [
    "price", "square", "livingRoom", "drawingRoom", "bathRoom",
    "constructionTime", "ladderRatio", "DOM", "followers",
    "Lng", "Lat", "communityAverage", "totalPrice"
]
numeric_cols = [c for c in numeric_cols if c in df.columns]
corr = df[numeric_cols].corr()

mask = np.triu(np.ones_like(corr, dtype=bool), k=1)
fig, ax = plt.subplots(figsize=(12, 10))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap=DIVERGING_CMAP,
            center=0, square=True, linewidths=0.5, vmin=-1, vmax=1,
            cbar_kws={"shrink": 0.8})
ax.set_title("数值变量 Pearson 相关系数矩阵")
save_fig("correlation_heatmap.png", "01_eda")

price_corr = corr["price"].drop("price", errors="ignore").sort_values(ascending=False)
print("与价格的相关性（降序）：")
for var, val in price_corr.items():
    print(f"  {var:20s}: {val:.4f}")

# ── 6. 地理分布 ──
print_section("6. 房价地理分布")

fig, ax = plt.subplots(figsize=(12, 10))
geo_sample = df.sample(min(10000, len(df)), random_state=42)
sc = ax.scatter(geo_sample["Lng"], geo_sample["Lat"],
                c=geo_sample["price"], cmap=SEQUENTIAL_CMAP,
                alpha=0.5, s=5, vmin=0, vmax=np.percentile(df["price"], 98))
plt.colorbar(sc, ax=ax, label="单价（元/㎡）")
ax.set_xlabel("经度")
ax.set_ylabel("纬度")
ax.set_title("北京房价地理分布（抽样 1 万条）")
save_fig("geo_price_scatter.png", "01_eda")

# ── 7. 各区域价格 ──
print_section("7. 各区域价格对比")

dist_mean = df.groupby("district")["price"].agg(["mean", "median", "count", "std"])
dist_mean = dist_mean.sort_values("mean", ascending=False)
print(dist_mean.to_string())

fig, ax = plt.subplots(figsize=(12, 5))
ax.bar(range(len(dist_mean)), dist_mean["mean"], color=CB_PALETTE[0], alpha=0.8)
ax.set_xticks(range(len(dist_mean)))
ax.set_xticklabels(dist_mean.index, rotation=45, ha="right")
ax.set_ylabel("平均单价（元/㎡）")
ax.set_title("各区域平均单价")
for i, (idx, row) in enumerate(dist_mean.iterrows()):
    ax.text(i, row["mean"] + 500, f"n={int(row['count']):,}", ha="center", fontsize=7)
save_fig("price_by_district.png", "01_eda")

# ── 8. 价格时间趋势 ──
print_section("8. 价格时间趋势")

df["trade_year"] = pd.to_datetime(df["tradeTime"], errors="coerce").dt.year
df = df[df["trade_year"].between(2011, 2017)].copy()
print(f"过滤交易年份后：{len(df):,} 行（2011-2017）")

yearly = df.groupby("trade_year")["price"].agg(["mean", "median", "count", "std"])
yearly = yearly.dropna()
print(yearly.to_string())

fig, ax1 = plt.subplots(figsize=(10, 5))
ax1.plot(yearly.index, yearly["mean"], "o-", color=CB_PALETTE[0], label="平均价格", linewidth=2)
ax1.plot(yearly.index, yearly["median"], "s--", color=CB_PALETTE[1], label="中位数价格", linewidth=2)
ax1.fill_between(yearly.index,
                  yearly["mean"] - yearly["std"],
                  yearly["mean"] + yearly["std"],
                  alpha=0.15, color=CB_PALETTE[0], label="±1 标准差")
ax1.set_xlabel("年份")
ax1.set_ylabel("单价（元/㎡）")
ax1.set_title("北京房价走势 (2011-2017)")
ax1.legend(loc="upper left")

ax2 = ax1.twinx()
ax2.bar(yearly.index, yearly["count"], alpha=0.15, color=CB_PALETTE[2], label="交易量")
ax2.set_ylabel("交易量")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
save_fig("price_trend_by_year.png", "01_eda")

# ── 9. 分类变量对比 ──
print_section("9. 分类变量对比")

cat_vars = [
    ("subway", "是否近地铁"),
    ("elevator", "是否有电梯"),
    ("fiveYearsProperty", "是否满五年"),
    ("buildingType", "建筑类型"),
    ("renovationCondition", "装修情况"),
    ("buildingStructure", "建筑结构"),
]
for col, label in cat_vars:
    if col not in df.columns or df[col].nunique() > 15:
        continue
    fig, ax = plt.subplots(figsize=(8, 4))
    df.boxplot(column="price", by=col, ax=ax, grid=False, patch_artist=True)
    ax.set_title(f"不同 {label} 的房价分布")
    ax.set_ylabel("单价（元/㎡）")
    ax.set_xlabel(label)
    fig.suptitle("")
    save_fig(f"price_by_{col}.png", "01_eda")

# ── 10. 数值变量分布 ──
print_section("10. 数值变量分布")

num_plot_cols = ["square", "DOM", "followers", "constructionTime", "ladderRatio"]
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()
for i, col in enumerate(num_plot_cols):
    if col not in df.columns:
        continue
    if col == "DOM":
        valid = df[col].dropna()
        valid = valid[valid < valid.quantile(0.99)]
    elif col == "followers":
        valid = df[col]
        valid = valid[valid < valid.quantile(0.99)]
    elif col == "ladderRatio":
        valid = df[col].dropna()
        valid = valid[valid < valid.quantile(0.99)]
    elif col == "constructionTime":
        valid = df[col].dropna()
    else:
        valid = df[col].dropna()
    axes[i].hist(valid, bins=60, color=CB_PALETTE[0], edgecolor="white", alpha=0.8)
    axes[i].set_xlabel(col)
    axes[i].set_ylabel("频数")
    axes[i].set_title(f"{col} 的分布")
axes[-1].set_visible(False)
save_fig("numeric_distributions.png", "01_eda")

# ── 11. 关键变量散点图矩阵 ──
print_section("11. 关键变量散点图矩阵（抽样）")

pair_cols = ["price", "square", "constructionTime", "Lng", "Lat"]
pair_df = df[pair_cols].dropna().sample(min(5000, len(df)), random_state=42)
pair_df["log_price"] = np.log(pair_df["price"])
sns.pairplot(pair_df.drop(columns=["price"]), diag_kind="kde",
             plot_kws={"alpha": 0.3, "s": 5})
save_fig("pairplot_key_vars.png", "01_eda")

# ── 12. 关键数值结果 ──
print_section("12. 关键数值结果")
print(f"""
数据集：{len(df):,} 条交易，{int(df['trade_year'].min())}-{int(df['trade_year'].max())} 年，{df['district'].nunique()} 个区域
价格均值={df['price'].mean():.1f}，中位数={df['price'].median():.1f}，偏度={df['price'].skew():.2f}（对数后：{log_price.skew():.2f}）
与价格相关性最高：communityAverage={price_corr.get('communityAverage', 'N/A'):.4f}，totalPrice={price_corr.get('totalPrice', 'N/A'):.4f}
""")

print("脚本 01 完成。所有图片已保存至 output/figures/01_eda/")
