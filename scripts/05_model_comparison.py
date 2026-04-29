"""
脚本 5：多模型比较
====================
目标：比较 6 种回归模型在测试集上的表现。
模型：
  1. OLS（全变量）
  2. Ridge 回归（CV 选 lambda）
  3. LASSO 回归（CV 选 lambda）
  4. OLS（脚本 3 筛选的共识变量）
  5. OLS + 交互项（关键数值变量）
  6. OLS + 多项式项（关键数值变量，degree=2）
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
from sklearn.linear_model import LinearRegression, RidgeCV, LassoCV
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import KFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import logging
logging.getLogger("statsmodels").setLevel(logging.WARNING)

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
X_train_scaled, X_test_scaled, numeric_cols, dummy_cols = joblib.load("output/scaled_data.pkl")
selection_results = joblib.load("output/selection_results.pkl")
consensus_vars = selection_results["consensus_vars"]

print(f"训练集：{X_train.shape[0]:,} 行 x {X_train.shape[1]} 个特征")
print(f"测试集：{X_test.shape[0]:,} 行")
print(f"共识变量：{len(consensus_vars)} 个")

# ── 2. 定义交互/多项式变量 ──
print_section("2. 选择交互/多项式变量")

key_interact_vars = ["dist_center", "Lat", "Lng", "trade_year", "ladderRatio", "DOM"]
key_interact_vars = [v for v in key_interact_vars if v in feature_cols]
print(f"选中的交互变量（{len(key_interact_vars)} 个）：{key_interact_vars}")

# 剩余变量（未参与交互/多项式变换）
remaining_vars = [v for v in feature_cols if v not in key_interact_vars]
print(f"剩余变量：{len(remaining_vars)} 个")

# ── 3. 定义模型训练与评估函数 ──
print_section("3. 拟合模型并评估")

test_metrics = []
cv_metrics = []
models_fitted = {}


def evaluate_model(name, y_true, y_pred, n_params=None):
    """计算评估指标。"""
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mae = mean_absolute_error(y_true, y_pred)
    # 反变换回价格尺度
    y_true_price = np.exp(y_true)
    y_pred_price = np.exp(y_pred)
    rmse_price = np.sqrt(mean_squared_error(y_true_price, y_pred_price))
    mae_price = mean_absolute_error(y_true_price, y_pred_price)

    result = {
        "Model": name, "R2": round(r2, 4), "RMSE": round(rmse, 4), "MAE": round(mae, 4),
        "RMSE_price": round(rmse_price, 1), "MAE_price": round(mae_price, 1)
    }
    # AIC/BIC 仅对 OLS 模型适用
    if n_params is not None:
        n = len(y_true)
        rss = np.sum((y_true - y_pred)**2)
        aic = n * np.log(rss / n) + 2 * n_params
        bic = n * np.log(rss / n) + n_params * np.log(n)
        result["AIC"] = round(aic, 1)
        result["BIC"] = round(bic, 1)

    return result


# ── 3a. OLS 全变量 ──
print("拟合 OLS（全变量）...")
t1 = time.time()
X_train_c = sm.add_constant(X_train)
ols_full = sm.OLS(y_train, X_train_c).fit()
X_test_c = sm.add_constant(X_test)
y_pred_full = ols_full.predict(X_test_c)
res = evaluate_model("OLS（全变量）", y_test, y_pred_full, n_params=X_train_c.shape[1])
test_metrics.append(res)
print(f"  R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f}, AIC={res['AIC']:.0f} 用时：{time.time()-t1:.1f}s")

# ── 3b. Ridge（CV）──
print("拟合 Ridge（CV）...")
t1 = time.time()
ridge_cv = RidgeCV(alphas=np.logspace(-3, 3, 50), cv=5)
ridge_cv.fit(X_train_scaled, y_train)
y_pred_ridge = ridge_cv.predict(X_test_scaled)
res = evaluate_model("Ridge（CV）", y_test, y_pred_ridge)
test_metrics.append(res)
models_fitted["Ridge"] = ridge_cv
print(f"  alpha={ridge_cv.alpha_:.4f}, R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f} 用时：{time.time()-t1:.1f}s")

# ── 3c. LASSO（CV）──
print("拟合 LASSO（CV）...")
t1 = time.time()
lasso_cv = LassoCV(alphas=np.logspace(-4, 0, 100), cv=5, max_iter=10000, random_state=SEED)
lasso_cv.fit(X_train_scaled, y_train)
y_pred_lasso = lasso_cv.predict(X_test_scaled)
res = evaluate_model("LASSO（CV）", y_test, y_pred_lasso)
test_metrics.append(res)
models_fitted["LASSO"] = lasso_cv
n_nonzero = np.sum(lasso_cv.coef_ != 0)
print(f"  alpha={lasso_cv.alpha_:.6f}, 非零系数={n_nonzero}/{len(feature_cols)}, R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f} 用时：{time.time()-t1:.1f}s")

# ── 3d. OLS 共识变量 ──
print("拟合 OLS（共识变量）...")
t1 = time.time()
X_train_sel = sm.add_constant(X_train[consensus_vars])
ols_sel = sm.OLS(y_train, X_train_sel).fit()
X_test_sel = sm.add_constant(X_test[consensus_vars])
y_pred_sel = ols_sel.predict(X_test_sel)
res = evaluate_model("OLS（筛选变量）", y_test, y_pred_sel, n_params=X_train_sel.shape[1])
test_metrics.append(res)
print(f"  R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f}, AIC={res['AIC']:.0f} 用时：{time.time()-t1:.1f}s")

# ── 3e. OLS + 交互项 ──
print("拟合 OLS + 交互项...")
t1 = time.time()
poly_interact = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
X_train_interact = np.hstack([
    X_train[remaining_vars].values,
    poly_interact.fit_transform(X_train[key_interact_vars].values)
])
X_test_interact = np.hstack([
    X_test[remaining_vars].values,
    poly_interact.transform(X_test[key_interact_vars].values)
])
# 创建特征名
interact_feat_names = remaining_vars + poly_interact.get_feature_names_out(key_interact_vars).tolist()
X_train_i_c = sm.add_constant(pd.DataFrame(X_train_interact, columns=interact_feat_names, index=X_train.index))
ols_interact = sm.OLS(y_train, X_train_i_c).fit()
X_test_i_c = sm.add_constant(pd.DataFrame(X_test_interact, columns=interact_feat_names, index=X_test.index))
y_pred_interact = ols_interact.predict(X_test_i_c)
res = evaluate_model("OLS + 交互项", y_test, y_pred_interact, n_params=X_train_i_c.shape[1])
test_metrics.append(res)
print(f"  特征数={X_train_i_c.shape[1]-1}, R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f}, AIC={res['AIC']:.0f} 用时：{time.time()-t1:.1f}s")

# ── 3f. OLS + 多项式 ──
print("拟合 OLS + 多项式（degree=2）...")
t1 = time.time()
poly_full = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
X_train_poly = np.hstack([
    X_train[remaining_vars].values,
    poly_full.fit_transform(X_train[key_interact_vars].values)
])
X_test_poly = np.hstack([
    X_test[remaining_vars].values,
    poly_full.transform(X_test[key_interact_vars].values)
])
poly_feat_names = remaining_vars + poly_full.get_feature_names_out(key_interact_vars).tolist()
X_train_p_c = sm.add_constant(pd.DataFrame(X_train_poly, columns=poly_feat_names, index=X_train.index))
ols_poly = sm.OLS(y_train, X_train_p_c).fit()
X_test_p_c = sm.add_constant(pd.DataFrame(X_test_poly, columns=poly_feat_names, index=X_test.index))
y_pred_poly = ols_poly.predict(X_test_p_c)
res = evaluate_model("OLS + 多项式", y_test, y_pred_poly, n_params=X_train_p_c.shape[1])
test_metrics.append(res)
print(f"  特征数={X_train_p_c.shape[1]-1}, R2={res['R2']:.4f}, RMSE={res['RMSE_price']:.1f}, AIC={res['AIC']:.0f} 用时：{time.time()-t1:.1f}s")

# ── 4. 测试集结果汇总 ──
print_section("4. 测试集结果汇总")
results_df = pd.DataFrame(test_metrics)
results_df = results_df.sort_values("R2", ascending=False)
save_table(results_df, "model_comparison.csv")
print(results_df.to_string(index=False))

# ── 5. 交叉验证比较 ──
print_section("5. 交叉验证（5折）")

cv_folds = 5
kf = KFold(n_splits=cv_folds, shuffle=True, random_state=SEED)
cv_results = []

# OLS 全变量
t1 = time.time()
lr = LinearRegression()
cv_r2 = cross_val_score(lr, X_train, y_train, cv=kf, scoring="r2")
cv_rmse = np.sqrt(-cross_val_score(lr, X_train, y_train, cv=kf, scoring="neg_mean_squared_error"))
cv_results.append({"Model": "OLS（全变量）", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  OLS（全变量）：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

# Ridge
t1 = time.time()
ridge_pipe = Pipeline([("scale", StandardScaler()), ("ridge", RidgeCV(alphas=np.logspace(-3, 3, 50), cv=3))])
cv_r2 = cross_val_score(ridge_pipe, X_train, y_train, cv=kf, scoring="r2")
cv_rmse = np.sqrt(-cross_val_score(ridge_pipe, X_train, y_train, cv=kf, scoring="neg_mean_squared_error"))
cv_results.append({"Model": "Ridge（CV）", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  Ridge（CV）：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

# LASSO
t1 = time.time()
lasso_pipe = Pipeline([
    ("scale", StandardScaler()),
    ("lasso", LassoCV(alphas=np.logspace(-4, 0, 100), cv=3, max_iter=10000, random_state=SEED))
])
cv_r2 = cross_val_score(lasso_pipe, X_train, y_train, cv=kf, scoring="r2")
cv_rmse = np.sqrt(-cross_val_score(lasso_pipe, X_train, y_train, cv=kf, scoring="neg_mean_squared_error"))
cv_results.append({"Model": "LASSO（CV）", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  LASSO（CV）：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

# OLS 共识变量
t1 = time.time()
lr_sel = LinearRegression()
cv_r2 = cross_val_score(lr_sel, X_train[consensus_vars], y_train, cv=kf, scoring="r2")
cv_rmse = np.sqrt(-cross_val_score(lr_sel, X_train[consensus_vars], y_train, cv=kf, scoring="neg_mean_squared_error"))
cv_results.append({"Model": "OLS（筛选变量）", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  OLS（筛选变量）：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

# OLS + 交互项
t1 = time.time()
cv_r2_list, cv_rmse_list = [], []
for train_idx, val_idx in kf.split(X_train):
    X_tr, X_val = X_train_interact[train_idx], X_train_interact[val_idx]
    y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
    lr_cv = LinearRegression().fit(X_tr, y_tr)
    y_p = lr_cv.predict(X_val)
    cv_r2_list.append(r2_score(y_val, y_p))
    cv_rmse_list.append(np.sqrt(mean_squared_error(y_val, y_p)))
cv_r2 = np.array(cv_r2_list); cv_rmse = np.array(cv_rmse_list)
cv_results.append({"Model": "OLS + 交互项", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  OLS + 交互项：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

# OLS + 多项式
t1 = time.time()
cv_r2_list, cv_rmse_list = [], []
for train_idx, val_idx in kf.split(X_train):
    X_tr, X_val = X_train_poly[train_idx], X_train_poly[val_idx]
    y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
    lr_cv = LinearRegression().fit(X_tr, y_tr)
    y_p = lr_cv.predict(X_val)
    cv_r2_list.append(r2_score(y_val, y_p))
    cv_rmse_list.append(np.sqrt(mean_squared_error(y_val, y_p)))
cv_r2 = np.array(cv_r2_list); cv_rmse = np.array(cv_rmse_list)
cv_results.append({"Model": "OLS + 多项式", "CV_R2": f"{cv_r2.mean():.4f}±{cv_r2.std():.4f}", "CV_RMSE": f"{cv_rmse.mean():.4f}±{cv_rmse.std():.4f}"})
print(f"  OLS + 多项式：R2={cv_r2.mean():.4f}±{cv_r2.std():.4f}, RMSE={cv_rmse.mean():.4f}±{cv_rmse.std():.4f} 用时：{time.time()-t1:.1f}s")

cv_df = pd.DataFrame(cv_results)
save_table(cv_df, "cv_comparison.csv")
print("\n交叉验证结果：")
print(cv_df.to_string(index=False))

# ── 6. 可视化：模型比较柱状图 ──
print_section("6. 可视化")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 测试集 R²
models_name = results_df["Model"].tolist()
r2_vals = results_df["R2"].tolist()
rmse_vals = results_df["RMSE_price"].tolist()

colors = [CB_PALETTE[0]] * len(models_name)
# 最优模型高亮
best_r2_idx = np.argmax(r2_vals)
colors[best_r2_idx] = CB_PALETTE[1]

axes[0].barh(range(len(models_name)), r2_vals, color=colors[::-1], alpha=0.8)
axes[0].set_yticks(range(len(models_name)))
axes[0].set_yticklabels(models_name[::-1])
axes[0].set_xlabel("R²")
axes[0].set_title("测试集 R² 比较")
for i, v in enumerate(r2_vals):
    axes[0].text(v + 0.002, len(models_name) - 1 - i, f"{v:.4f}", va="center", fontsize=9)

# 测试集 RMSE（价格尺度）
colors_rmse = [CB_PALETTE[0]] * len(models_name)
best_rmse_idx = np.argmin(rmse_vals)
colors_rmse[best_rmse_idx] = CB_PALETTE[1]

axes[1].barh(range(len(models_name)), rmse_vals, color=colors_rmse[::-1], alpha=0.8)
axes[1].set_yticks(range(len(models_name)))
axes[1].set_yticklabels(models_name[::-1])
axes[1].set_xlabel("RMSE（元/㎡）")
axes[1].set_title("测试集 RMSE 比较")
for i, v in enumerate(rmse_vals):
    axes[1].text(v + 100, len(models_name) - 1 - i, f"{v:.0f}", va="center", fontsize=9)

save_fig("model_comparison.png", "05_comparison")

# ── 7. 最佳模型系数图 ──
print_section("7. 最佳模型系数")
# 选出最优 OLS 模型（排除 Ridge/LASSO 因尺度不同不好直接比系数）
best_ols_name = results_df[~results_df["Model"].str.contains("Ridge|LASSO")].iloc[0]["Model"]
print(f"最佳 OLS 模型：{best_ols_name}")

# 获取对应的模型和特征名
if "交互" in best_ols_name:
    best_ols = ols_interact
    best_feat_names = interact_feat_names
elif "多项式" in best_ols_name:
    best_ols = ols_poly
    best_feat_names = poly_feat_names
elif "筛选" in best_ols_name:
    best_ols = ols_sel
    best_feat_names = consensus_vars
else:
    best_ols = ols_full
    best_feat_names = feature_cols

# 绘制前 15 个系数的条形图（按绝对值）
coef_series = pd.Series(best_ols.params.drop("const", errors="ignore"), index=best_feat_names[:len(best_ols.params)-1])
top_coefs = coef_series.abs().sort_values(ascending=False).head(15)
top_coef_vals = coef_series[top_coefs.index]

fig, ax = plt.subplots(figsize=(10, 7))
colors_coef = [CB_PALETTE[1] if v > 0 else CB_PALETTE[0] for v in top_coef_vals]
ax.barh(range(len(top_coef_vals)), top_coef_vals, color=colors_coef[::-1], alpha=0.8)
ax.set_yticks(range(len(top_coef_vals)))
ax.set_yticklabels(top_coefs.index[::-1], fontsize=9)
ax.axvline(x=0, color="gray", linestyle="-", linewidth=0.5)
ax.set_xlabel("系数")
ax.set_title(f"最佳模型系数（{best_ols_name}，前 15 名）")
save_fig(f"best_model_coefficients.png", "05_comparison")

# ── 8. 关键数值结果 ──
print_section("8. 关键数值结果")
print(f"""
最佳模型：{results_df.iloc[0]['Model']}
测试集 R2={results_df.iloc[0]['R2']:.4f}, RMSE={results_df.iloc[0]['RMSE_price']:.1f} 元/㎡, MAE={results_df.iloc[0]['MAE_price']:.1f} 元/㎡

各模型表现排名：
""")
for i, row in results_df.iterrows():
    print(f"  {i+1}. {row['Model']:20s}  R2={row['R2']:.4f}  RMSE={row['RMSE_price']:.1f}  MAE={row['MAE_price']:.1f}")

print(f"\n脚本 05 完成，总用时：{time.time() - t0:.1f}s")
