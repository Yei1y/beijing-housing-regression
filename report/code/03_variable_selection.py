import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings
warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import statsmodels.api as sm
from sklearn.linear_model import LassoCV, Lasso
import logging
logging.getLogger("statsmodels").setLevel(logging.WARNING)
from utils import (
    setup_font, print_section, save_fig, save_table, CB_PALETTE
)
setup_font()
SEED = 42
np.random.seed(SEED)
print_section("1. 加载预处理后的数据")
X_train, X_test, y_train, y_test, feature_cols = joblib.load("output/processed_data.pkl")
X_train_scaled, X_test_scaled, numeric_cols, dummy_cols = joblib.load("output/scaled_data.pkl")
print(f"全量训练集：{X_train.shape[0]:,} 行 x {X_train.shape[1]} 个特征")
print_section("2. 向前选择（基于 AIC，子样本）")
subsample_size = min(20000, len(X_train))
idx_sub = np.random.choice(X_train.index, subsample_size, replace=False)
X_sub = X_train.loc[idx_sub]
y_sub = y_train.loc[idx_sub]
print(f"子样本：{subsample_size:,} 行")
def forward_selection_aic(X, y, max_features=30):
    remaining = list(X.columns)
    selected = []
    current_aic = np.inf
    history = []
    for step in range(max_features):
        if not remaining:
            break
        best_var = None
        best_aic = np.inf
        best_model = None
        for var in remaining:
            cols = selected + [var]
            X_subset = sm.add_constant(X[cols])
            try:
                model = sm.OLS(y, X_subset).fit()
                if model.aic < best_aic:
                    best_aic = model.aic
                    best_var = var
                    best_model = model
            except Exception:
                continue
        if best_aic < current_aic - 1e-6:
            selected.append(best_var)
            remaining.remove(best_var)
            current_aic = best_aic
            history.append({"step": step + 1, "var": best_var, "aic": best_aic,
                            "rsquared": best_model.rsquared})
            print(f"  第{step+1:2d}步：+ {best_var:35s}  AIC={best_aic:.1f},  R2={best_model.rsquared:.4f}")
        else:
            print(f"  在第 {step} 步停止：AIC 不再改善")
            break
    return selected, pd.DataFrame(history)
selected_forward, fwd_history = forward_selection_aic(X_sub, y_sub)
print(f"\n向前选择完毕：{len(selected_forward)} 个变量")
print_section("3. 向后剔除（基于 AIC，子样本）")
def backward_elimination_aic(X, y, max_iter=60):
    cols = list(X.columns)
    history = []
    for step in range(max_iter):
        if len(cols) <= 1:
            break
        X_subset = sm.add_constant(X[cols])
        try:
            model = sm.OLS(y, X_subset).fit()
        except Exception:
            break
        current_aic = model.aic
        pvalues = model.pvalues.drop("const", errors="ignore")
        worst_var = pvalues.idxmax()
        worst_pval = pvalues.max()
        cols_reduced = [c for c in cols if c != worst_var]
        X_reduced = sm.add_constant(X[cols_reduced])
        try:
            model_reduced = sm.OLS(y, X_reduced).fit()
            if model_reduced.aic <= current_aic + 1e-6:
                cols = cols_reduced
                history.append({"step": step + 1, "removed": worst_var,
                                "pval": worst_pval, "aic": model_reduced.aic,
                                "rsquared": model_reduced.rsquared})
                print(f"  第{step+1:2d}步：- {worst_var:35s}  p={worst_pval:.6f}, AIC={model_reduced.aic:.1f}")
            else:
                print(f"  停止：剔除 {worst_var} 使 AIC 上升")
                break
        except Exception:
            break
    return cols, pd.DataFrame(history)
selected_backward, bwd_history = backward_elimination_aic(X_sub, y_sub)
print(f"\n向后剔除完毕：{len(selected_backward)} 个变量保留")
print_section("4. LASSO 正则化（全量数据）")
lasso_cv = LassoCV(
    alphas=np.logspace(-4, 0, 100),
    cv=5,
    max_iter=10000,
    random_state=SEED,
    n_jobs=-1
)
lasso_cv.fit(X_train_scaled, y_train)
print(f"最优 alpha：{lasso_cv.alpha_:.6f}")
print(f"非零系数：{np.sum(lasso_cv.coef_ != 0)} / {len(feature_cols)}")
alphas = lasso_cv.alphas_
coef_path = []
for alpha in alphas:
    lasso = Lasso(alpha=alpha, max_iter=10000)
    lasso.fit(X_train_scaled, y_train)
    coef_path.append(lasso.coef_)
coef_path = np.array(coef_path)
top10_idx = np.argsort(np.abs(lasso_cv.coef_))[-10:]
top10_names = [feature_cols[i] for i in top10_idx]
fig, ax = plt.subplots(figsize=(12, 6))
for rank, i in enumerate(top10_idx):
    color = CB_PALETTE[rank % len(CB_PALETTE)]
    ax.plot(np.log10(alphas), coef_path[:, i],
            alpha=0.8, linewidth=1.2, color=color,
            label=feature_cols[i])
ax.axvline(np.log10(lasso_cv.alpha_), color="red", linestyle="--",
           label=f"最优 alpha = {lasso_cv.alpha_:.6f}")
ax.set_xlabel("log(alpha)")
ax.set_ylabel("系数值")
ax.set_title("LASSO 正则化路径（前 10 个变量）")
ax.legend(loc="best", fontsize=8, ncol=2)
save_fig("lasso_path.png", "03_selection")
lasso_coef = pd.Series(lasso_cv.coef_, index=feature_cols)
lasso_selected = list(lasso_coef[abs(lasso_coef) > 1e-4].sort_values(key=abs, ascending=False).index)
print(f"\nLASSO 系数绝对值前 15 名：")
for var, coef in lasso_coef[abs(lasso_coef) > 1e-4].abs().sort_values(ascending=False).head(15).items():
    print(f"  {var:35s}: {lasso_cv.coef_[feature_cols.index(var)]:+.6f}")
print_section("5. 比较三种选择方法")
var_list = []
for v in feature_cols:
    row = {"Variable": v,
           "Forward": 1 if v in selected_forward else 0,
           "Backward": 1 if v in selected_backward else 0,
           "LASSO": 1 if abs(lasso_cv.coef_[feature_cols.index(v)]) > 1e-4 else 0}
    var_list.append(row)
comparison = pd.DataFrame(var_list)
comparison["Agreement"] = comparison[["Forward", "Backward", "LASSO"]].sum(axis=1)
comparison = comparison.sort_values(["Agreement", "Variable"], ascending=[False, True])
comparison["Selected"] = comparison["Agreement"] >= 2
save_table(comparison, "selection_comparison.csv")
print("三种方法一致性比较（被至少 2 种方法选中的变量）：")
selected_by_consensus = comparison[comparison["Agreement"] >= 2]
print(selected_by_consensus[["Variable", "Forward", "Backward", "LASSO", "Agreement"]].to_string())
print_section("6. 基于共识变量的 OLS 模型（一致性 >= 2）")
consensus_vars = comparison[comparison["Agreement"] >= 2]["Variable"].tolist()
print(f"共识变量（{len(consensus_vars)} 个）：")
for v in consensus_vars:
    print(f"  - {v}")
if len(consensus_vars) == 0:
    print("警告：无变量被至少 2 种方法选中，回退到 LASSO 选中的变量。")
    consensus_vars = lasso_selected[:20]
X_train_consensus = sm.add_constant(X_train[consensus_vars])
ols_consensus = sm.OLS(y_train, X_train_consensus).fit()
print(f"\nOLS R2：{ols_consensus.rsquared:.4f}")
print(f"OLS 调整 R2：{ols_consensus.rsquared_adj:.4f}")
print(f"AIC：{ols_consensus.aic:.1f}")
print(f"\|系数|前十：")
coef_df = pd.DataFrame({
    "Variable": ols_consensus.params.index,
    "Coefficient": ols_consensus.params.values,
    "P-value": ols_consensus.pvalues.values,
    "Significant": ols_consensus.pvalues.values < 0.05
}).sort_values("Coefficient", key=abs, ascending=False)
print(coef_df.head(10).to_string())
save_table(coef_df, "consensus_ols_coefficients.csv")
print_section("7. 保存选择结果")
selection_results = {
    "selected_forward": selected_forward,
    "selected_backward": selected_backward,
    "lasso_selected": lasso_selected,
    "consensus_vars": consensus_vars,
}
joblib.dump(selection_results, "output/selection_results.pkl")
print("已保存：output/selection_results.pkl")
print_section("8. 关键数值结果")
print(f"""
向前选择：{len(selected_forward)} 个 | 向后剔除：{len(selected_backward)} 个保留 | LASSO：{len(lasso_selected)} 个非零系数（alpha={lasso_cv.alpha_:.6f}）
共识变量（≥2 种方法）：{len(consensus_vars)} 个
