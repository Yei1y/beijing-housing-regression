"""
脚本 4：模型诊断
==================
目标：检验 OLS 假设条件，诊断模型问题。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.filterwarnings("ignore")

import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.diagnostic import het_breuschpagan, het_goldfeldquandt
from statsmodels.stats.stattools import durbin_watson
import logging
logging.getLogger("statsmodels").setLevel(logging.WARNING)

from sklearn.preprocessing import PolynomialFeatures

from utils import (
    setup_font, print_section, save_fig, save_table, CB_PALETTE
)

setup_font()
SEED = 42
np.random.seed(SEED)

t0 = time.time()

# ── 1. 加载数据 ──
print_section("1. 加载数据")
X_train, X_test, y_train, y_test, feature_cols = joblib.load("output/processed_data.pkl")
print(f"训练集：{X_train.shape[0]:,} 行 x {X_train.shape[1]} 个特征")
print(f"测试集：{X_test.shape[0]:,} 行")

# ── 2. 拟合全变量 OLS 模型 ──
print_section("2. 全变量 OLS 模型")

diag_sample = min(20000, len(X_train))
idx_diag = np.random.choice(X_train.index, diag_sample, replace=False)
X_diag = X_train.loc[idx_diag]
y_diag = y_train.loc[idx_diag]

print(f"在 {diag_sample:,} 行上用 {len(feature_cols)} 个特征拟合 OLS...")

X_diag_const = sm.add_constant(X_diag)
ols_full = sm.OLS(y_diag, X_diag_const).fit()
print(ols_full.summary())
print(f"  OLS 拟合用时：{time.time() - t0:.1f}s")

t1 = time.time()

fitted = ols_full.fittedvalues
residuals = ols_full.resid

# 手动计算影响诊断指标，避免 statsmodels get_influence() 的性能问题
X_mat = X_diag_const.values.astype(np.float64)
n, p = X_mat.shape

inv_xtx = np.asarray(ols_full.normalized_cov_params)  # (X'X)^{-1}
# 帽子矩阵对角元素 hii = diag(X (X'X)^{-1} X')
# 用 (X @ inv_xtx) * X 后按行求和，避免构建完整 n×n 矩阵
x_cov = X_mat @ inv_xtx  # n × p
hat_diag = (x_cov * X_mat).sum(axis=1)  # n 维向量
# 数值保护：防止 1 - hii 趋近 0
hat_diag = np.clip(hat_diag, 0, 1 - 1e-10)

resid_vals = residuals.values.ravel()
mse_resid = ols_full.mse_resid

# 学生化残差（内学生化）
resid_student = resid_vals / (np.sqrt(mse_resid) * np.sqrt(1 - hat_diag))

# 外学生化残差（leave-one-out）
sigma_i = np.sqrt(((n - p) / (n - p - 1)) * mse_resid -
                   resid_vals**2 / ((n - p - 1) * (1 - hat_diag)))
studentized_resid = resid_vals / (sigma_i * np.sqrt(1 - hat_diag))

# Cook's distance
cooks = studentized_resid**2 / p * hat_diag / (1 - hat_diag)

leverage = hat_diag

print(f"  影响诊断计算用时：{time.time() - t1:.1f}s")

# ── 3. 残差分析 ──
t1 = time.time()
print_section("3. 残差分析")

plot_n = min(10000, diag_sample)
plot_idx = np.random.choice(diag_sample, plot_n, replace=False)

fig, axes = plt.subplots(2, 3, figsize=(16, 10))

# (1) 残差 vs 拟合值
axes[0, 0].scatter(fitted.iloc[plot_idx], residuals.iloc[plot_idx],
                   alpha=0.3, s=2, color=CB_PALETTE[0])
axes[0, 0].axhline(y=0, color="red", linestyle="--", linewidth=1)
axes[0, 0].set_xlabel("拟合值")
axes[0, 0].set_ylabel("残差")
axes[0, 0].set_title("残差 vs 拟合值")

# (2) Q-Q 图
stats.probplot(residuals, dist="norm", plot=axes[0, 1])
axes[0, 1].get_lines()[0].set_markersize(1)
axes[0, 1].get_lines()[0].set_markeredgecolor(CB_PALETTE[0])
axes[0, 1].get_lines()[1].set_color("red")
axes[0, 1].set_title("正态 Q-Q 图")

# (3) 尺度-位置图
axes[0, 2].scatter(fitted.iloc[plot_idx],
                   np.sqrt(np.abs(studentized_resid[plot_idx])),
                   alpha=0.3, s=2, color=CB_PALETTE[1])
axes[0, 2].set_xlabel("拟合值")
axes[0, 2].set_ylabel("sqrt(|标准化残差|)")
axes[0, 2].set_title("尺度-位置图")

# (4) 残差直方图
axes[1, 0].hist(residuals, bins=80, density=True, alpha=0.7, color=CB_PALETTE[0], edgecolor="white")
x_range = np.linspace(residuals.min(), residuals.max(), 100)
axes[1, 0].plot(x_range, stats.norm.pdf(x_range, residuals.mean(), residuals.std()),
                "r-", linewidth=2, label="正态拟合")
axes[1, 0].set_xlabel("残差")
axes[1, 0].set_ylabel("密度")
axes[1, 0].set_title("残差分布")
axes[1, 0].legend()

# (5) 残差 vs 杠杆值
axes[1, 1].scatter(leverage[plot_idx], studentized_resid[plot_idx],
                   alpha=0.3, s=2, color=CB_PALETTE[1])
axes[1, 1].axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
axes[1, 1].set_xlabel("杠杆值")
axes[1, 1].set_ylabel("学生化残差")
axes[1, 1].set_title("残差 vs 杠杆值")

# (6) 实际值 vs 预测值
axes[1, 2].scatter(y_diag.iloc[plot_idx], fitted.iloc[plot_idx],
                   alpha=0.3, s=2, color=CB_PALETTE[0])
axes[1, 2].plot([y_diag.min(), y_diag.max()],
                [y_diag.min(), y_diag.max()], "r--", linewidth=1)
axes[1, 2].set_xlabel("实际 log(价格)")
axes[1, 2].set_ylabel("预测 log(价格)")
axes[1, 2].set_title("实际值 vs 预测值")

save_fig("residual_diagnostics.png", "04_diagnostics")
print(f"  残差图绘图用时：{time.time() - t1:.1f}s")

# ── 4. 多重共线性（VIF）──
t1 = time.time()
print_section("4. 多重共线性（VIF）")

vif_sample = min(20000, len(X_train))
idx_vif = np.random.choice(X_train.index, vif_sample, replace=False)
X_vif = sm.add_constant(X_train.loc[idx_vif])

vif_data = []
for i in range(X_vif.shape[1]):
    vif_val = variance_inflation_factor(X_vif.values, i)
    vif_data.append({
        "Variable": X_vif.columns[i],
        "VIF": round(vif_val, 2),
        "VIF > 10": vif_val > 10
    })

vif_df = pd.DataFrame(vif_data).sort_values("VIF", ascending=False)
print(f"VIF 在 {vif_sample:,} 行上计算，共 {len(vif_df)} 个变量")
print("\nVIF 前 20 名：")
print(vif_df.head(20).to_string())
print(f"\nVIF > 10 的变量数：{vif_df['VIF > 10'].sum()}")

save_table(vif_df, "vif_results.csv")

# VIF 柱状图（top-20，排除常数项）
vif_no_const = vif_df[vif_df["Variable"] != "const"]
vif_top20 = vif_no_const.head(20).sort_values("VIF", ascending=True)
fig, ax = plt.subplots(figsize=(10, 8))
colors_vif = [CB_PALETTE[0] if v > 10 else CB_PALETTE[3]
              for v in vif_top20["VIF"]]
ax.barh(range(len(vif_top20)), vif_top20["VIF"], color=colors_vif, alpha=0.8)
ax.set_yticks(range(len(vif_top20)))
ax.set_yticklabels(vif_top20["Variable"], fontsize=9)
ax.axvline(x=10, color="red", linestyle="--", linewidth=1.5, label="VIF = 10 阈值")
ax.set_xlabel("VIF 值")
ax.set_title("方差膨胀因子（前 20 名变量）")
ax.legend()
save_fig("vif_bar_chart.png", "04_diagnostics")

print(f"  VIF 用时：{time.time() - t1:.1f}s")

# ── 4b. 多项式模型条件数 ──
t1 = time.time()
print_section("4b. 多项式模型条件数")

# 复用脚本05的多项式扩展逻辑
key_interact_vars = ["dist_center", "Lat", "Lng", "ladderRatio", "DOM"]
key_interact_vars = [v for v in key_interact_vars if v in feature_cols]
remaining_vars = [v for v in feature_cols if v not in key_interact_vars]

poly_full = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
X_poly = np.hstack([
    X_train[remaining_vars].values,
    poly_full.fit_transform(X_train[key_interact_vars].values)
])
poly_feat_names = remaining_vars + poly_full.get_feature_names_out(key_interact_vars).tolist()
X_poly_df = pd.DataFrame(X_poly, columns=poly_feat_names, index=X_train.index)

# 计算条件数（使用子样本以加速）
poly_sample = min(5000, len(X_poly_df))
idx_poly = np.random.choice(X_poly_df.index, poly_sample, replace=False)
X_poly_sub = X_poly_df.loc[idx_poly].values

# 标准化后计算条件数
X_poly_std = (X_poly_sub - X_poly_sub.mean(axis=0)) / (X_poly_sub.std(axis=0) + 1e-10)
cond_poly = np.linalg.cond(X_poly_std)
print(f"多项式模型特征数：{X_poly_df.shape[1]}")
print(f"条件数（5,000行子样本，标准化后）：{cond_poly:.2e}")

# 交互项模型条件数
poly_interact = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_interact = np.hstack([
    X_train[remaining_vars].values,
    poly_interact.fit_transform(X_train[key_interact_vars].values)
])
interact_feat_names = remaining_vars + poly_interact.get_feature_names_out(key_interact_vars).tolist()
X_interact_df = pd.DataFrame(X_interact, columns=interact_feat_names, index=X_train.index)

idx_int = np.random.choice(X_interact_df.index, poly_sample, replace=False)
X_int_sub = X_interact_df.loc[idx_int].values
X_int_std = (X_int_sub - X_int_sub.mean(axis=0)) / (X_int_sub.std(axis=0) + 1e-10)
cond_int = np.linalg.cond(X_int_std)
print(f"交互项模型特征数：{X_interact_df.shape[1]}")
print(f"条件数（5,000行子样本，标准化后）：{cond_int:.2e}")

print(f"  多项式条件数用时：{time.time() - t1:.1f}s")

# ── 5. 异方差检验 ──
t1 = time.time()
print_section("5. 异方差检验")

bp_test = het_breuschpagan(residuals, X_diag_const)
bp_stat, bp_pval, bp_fstat, bp_fpval = bp_test
print(f"Breusch-Pagan 检验：")
print(f"  LM 统计量：{bp_stat:.4f}")
print(f"  LM p 值：  {bp_pval:.6e}")
print(f"  F 统计量： {bp_fstat:.4f}")
print(f"  F p 值：   {bp_fpval:.6e}")

gq_test = het_goldfeldquandt(residuals, X_diag_const)
gq_stat, gq_pval, gq_alt = gq_test
print(f"\nGoldfeld-Quandt 检验：")
print(f"  F 统计量：{gq_stat:.4f}")
print(f"  p 值：    {gq_pval:.6e}")
print(f"  对立假设：{gq_alt}")

het_results = pd.DataFrame({
    "Test": ["Breusch-Pagan (LM)", "Breusch-Pagan (F)", "Goldfeld-Quandt"],
    "Statistic": [bp_stat, bp_fstat, gq_stat],
    "p-value": [bp_pval, bp_fpval, gq_pval],
    "Conclusion": [
        "异方差" if bp_pval < 0.05 else "同方差",
        "异方差" if bp_fpval < 0.05 else "同方差",
        "异方差" if gq_pval < 0.05 else "同方差",
    ]
})
save_table(het_results, "heteroscedasticity_tests.csv")
print(het_results.to_string())
print(f"  异方差检验用时：{time.time() - t1:.1f}s")

# ── 6. 自相关检验（Durbin-Watson）──
print_section("6. 自相关检验（Durbin-Watson）")

dw = durbin_watson(residuals)
print(f"Durbin-Watson 统计量：{dw:.4f}")
print(f"  DW = 2.0  -> 无自相关")
print(f"  DW < 1.5  -> 正自相关")
print(f"  DW > 2.5  -> 负自相关")
print(f"  结论：{'可能存在自相关' if abs(dw - 2) > 0.5 else '无严重自相关'}")

# ── 7. 强影响点分析 ──
t1 = time.time()
print_section("7. 强影响点分析")

n_obs = X_diag_const.shape[0]
n_params = X_diag_const.shape[1]
cooks_threshold = 4 / (n_obs - n_params - 1)
leverage_threshold = 2 * n_params / n_obs

n_influential_cooks = np.sum(cooks > cooks_threshold)
n_high_leverage = np.sum(leverage > leverage_threshold)

print(f"Cook's distance 阈值（4/(n-p-1)）：{cooks_threshold:.6f}")
print(f"  超过阈值的观测：{n_influential_cooks}（{100*n_influential_cooks/n_obs:.1f}%）")
print(f"杠杆值阈值（2p/n）：{leverage_threshold:.6f}")
print(f"  高杠杆值的观测：{n_high_leverage}（{100*n_high_leverage/n_obs:.1f}%）")

fig, axes = plt.subplots(1, 3, figsize=(16, 5))

# Cook's distance
axes[0].scatter(range(len(cooks)), cooks, s=1, alpha=0.4, color=CB_PALETTE[0])
axes[0].axhline(y=cooks_threshold, color="red", linestyle="--",
                label=f"阈值 = {cooks_threshold:.4f}")
axes[0].set_xlabel("观测序号")
axes[0].set_ylabel("Cook's Distance")
axes[0].set_title("Cook's Distance")
axes[0].legend()

# 杠杆值 vs 学生化残差
axes[1].scatter(leverage, studentized_resid, alpha=0.3, s=2, color=CB_PALETTE[1])
axes[1].axhline(y=0, color="gray", linestyle="--")
axes[1].axvline(x=leverage_threshold, color="red", linestyle="--",
                label=f"杠杆阈值 = {leverage_threshold:.4f}")
axes[1].set_xlabel("杠杆值")
axes[1].set_ylabel("学生化残差")
axes[1].set_title("杠杆值 vs 学生化残差")
axes[1].legend()

# 前 10 个最影响点
top10_idx = np.argsort(cooks)[-10:][::-1]
top10_labels = [f"观测 {i}" for i in top10_idx]
axes[2].barh(range(10), cooks[top10_idx], color=CB_PALETTE[2])
axes[2].set_yticks(range(10))
axes[2].set_yticklabels(top10_labels)
axes[2].set_xlabel("Cook's Distance")
axes[2].set_title("影响最大的前 10 个点")

save_fig("influential_points.png", "04_diagnostics")

influential_df = pd.DataFrame({
    "index": np.arange(len(cooks)),
    "cooks_d": cooks,
    "leverage": leverage,
    "student_resid": studentized_resid,
}).sort_values("cooks_d", ascending=False).head(10)

print("\n影响最大的前 10 个观测：")
print(influential_df.to_string())
print(f"  强影响点分析用时：{time.time() - t1:.1f}s")

# ── 8. 稳健标准误 ──
t1 = time.time()
print_section("8. 稳健标准误（HC3）")

ols_robust = sm.OLS(y_diag, X_diag_const).fit(cov_type="HC3")

se_comparison = pd.DataFrame({
    "Variable": ols_full.params.index,
    "Coef": ols_full.params.values,
    "SE_Regular": ols_full.bse.values,
    "SE_Robust": ols_robust.bse.values,
    "t_Robust": ols_robust.tvalues.values,
    "p_Robust": ols_robust.pvalues.values,
})
se_comparison["SE_Ratio"] = se_comparison["SE_Robust"] / se_comparison["SE_Regular"]

print("普通 vs 稳健标准误对比（按比率降序，前 15）：")
print(se_comparison.sort_values("SE_Ratio", ascending=False).head(15).to_string())

reg_sig = set(ols_full.pvalues[ols_full.pvalues < 0.05].index)
robust_sig = set(ols_robust.pvalues[ols_robust.pvalues < 0.05].index)
changed = reg_sig.symmetric_difference(robust_sig)
print(f"\n使用稳健标准误后显著性发生变化的变量：{len(changed)}")
if len(changed) > 0:
    for var in changed:
        print(f"  {var}: p_普通={ols_full.pvalues[var]:.6f}, p_稳健={ols_robust.pvalues[var]:.6f}")
print(f"  稳健标准误用时：{time.time() - t1:.1f}s")

# ── 9. 测试集验证 ──
t1 = time.time()
print_section("9. 测试集验证")

X_test_const = sm.add_constant(X_test)
y_pred_test = ols_full.predict(X_test_const)
test_residuals = y_test - y_pred_test

test_r2 = 1 - np.sum(test_residuals**2) / np.sum((y_test - y_test.mean())**2)
test_rmse = np.sqrt(np.mean(test_residuals**2))
test_mae = np.mean(np.abs(test_residuals))

print(f"测试集表现（对数尺度）：")
print(f"  R2：    {test_r2:.4f}")
print(f"  RMSE：  {test_rmse:.4f}")
print(f"  MAE：   {test_mae:.4f}")

# 反变换回原始尺度
y_test_price = np.exp(y_test)
y_pred_price = np.exp(y_pred_test)
test_rmse_price = np.sqrt(np.mean((y_test_price - y_pred_price)**2))
test_mae_price = np.mean(np.abs(y_test_price - y_pred_price))
print(f"\n反变换回价格尺度：")
print(f"  RMSE：  {test_rmse_price:.1f}")
print(f"  MAE：   {test_mae_price:.1f}")
print(f"  测试集验证用时：{time.time() - t1:.1f}s")

# ── 10. 关键数值结果 ──
print_section("10. 关键数值结果")

norm_stat, norm_pval = stats.normaltest(residuals)
print(f"""
残差正态性检验 p={norm_pval:.6e}
VIF > 10：{vif_df['VIF > 10'].sum()} 个变量 | 最大 VIF：{vif_df['VIF'].max():.1f}（{vif_df.iloc[0]['Variable']}）
条件数（全变量OLS）：{np.linalg.cond(X_diag.values):.2e}
条件数（多项式模型）：{cond_poly:.2e}
条件数（交互项模型）：{cond_int:.2e}
异方差：BP p={bp_pval:.6e} | GQ p={gq_pval:.6e}
自相关：DW={dw:.4f}
强影响点：{n_influential_cooks}（{100*n_influential_cooks/n_obs:.2f}%）超过 Cook's D 阈值
使用 HC3 稳健标准误后显著性改变的变量数：{len(changed)}
测试集：R2={test_r2:.4f}, RMSE={test_rmse_price:.1f}, MAE={test_mae_price:.1f}
""")

print(f"脚本 04 完成，总用时：{time.time() - t0:.1f}s")
