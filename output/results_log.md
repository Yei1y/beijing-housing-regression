# 结果记录

> 各分析脚本的关键数值输出记录。
> 更新日期：2026-05-26（新增多项式条件数、DOM稳健性检验）

---

## 脚本 01 — 探索性数据分析

**状态：** ✅ 已完成

| 指标 | 数值 |
|--------|-------|
| 交易总条数（过滤后） | 318,205（2011-2017） |
| 时间跨度 | 2011–2017 |
| 区域数量 | 13（district 编码） |
| 价格均值 | 43,568 元/㎡ |
| 价格中位数 | 38,754 元/㎡ |
| 价格偏度（原始） | 1.31 |
| 价格偏度（对数） | −0.59 |
| 与价格相关性最高 | communityAverage (0.685), totalPrice (0.622) |

### 已保存图片
- `output/figures/01_eda/price_distribution.png`
- `output/figures/01_eda/correlation_heatmap.png`
- `output/figures/01_eda/geo_price_scatter.png`
- `output/figures/01_eda/price_by_district.png`
- `output/figures/01_eda/price_trend_by_year.png`（已修复：仅显示 2011-2017）
- `output/figures/01_eda/price_by_*.png`（6 个分类变量对比）
- `output/figures/01_eda/numeric_distributions.png`
- `output/figures/01_eda/pairplot_key_vars.png`

---

## 脚本 02 — 数据预处理

**状态：** ✅ 已完成

| 指标 | 数值 |
|--------|-------|
| 训练样本 | 254,528 |
| 测试样本 | 63,632 |
| 特征总数 | 64（16 个数值型 + 48 个虚拟变量） |
| 时间固定效应 | trade_year（6 个虚拟变量）, trade_month（11 个虚拟变量） |
| Winsorize 截尾变量 | price(0.5%), square(0.5%), ladderRatio(1%), followers(1%), DOM(1%) |

### 已保存数据
- `output/processed_data.pkl` — 未标准化的训练/测试集 + 特征列表
- `output/scaled_data.pkl` — 标准化后的训练/测试集 + 列名
- `output/scaler.pkl` — StandardScaler 对象

---

## 脚本 03 — 变量选择

**状态：** ✅ 已完成

| 方法 | 选中变量数 |
|--------|-------------------|
| 向前选择（AIC） | 30 |
| 向后剔除（AIC） | 60 |
| LASSO（CV, alpha=0.0001） | 60 |
| 共识（≥2 种方法） | 59 |

### 已保存输出
- `output/selection_results.pkl`
- `output/tables/selection_comparison.csv`
- `output/tables/consensus_ols_coefficients.csv`
- `output/figures/03_selection/lasso_path.png`（已优化：仅显示 top-10 变量）

---

## 脚本 04 — 模型诊断

**状态：** ✅ 已完成（子样本 2 万行）

| 检验 | 结果 |
|------|--------|
| VIF > 10 变量数 | 9 |
| 最大 VIF（不含常数项） | 492.4（buildingStructure_6） |
| 条件数（全变量OLS） | 1.67e+04 |
| 条件数（多项式模型） | 1.11e+12 |
| 条件数（交互项模型） | 1.41e+16 |
| Breusch-Pagan p 值 | 1.8e-159（拒绝同方差） |
| Goldfeld-Quandt p 值 | 0.857（不拒绝同方差） |
| Durbin-Watson | 1.966（无自相关） |
| Cook's D 异常点（%） | 947（4.74%） |
| HC3 下显著性改变的变量 | 1（fiveYearsProperty_1.0） |
| 测试集 R² | 0.818（对数尺度） |
| 测试集 RMSE | 9,690 元/㎡ |
| 测试集 MAE | 6,704 元/㎡ |

### 已保存输出
- `output/figures/04_diagnostics/residual_diagnostics.png`
- `output/figures/04_diagnostics/influential_points.png`
- `output/figures/04_diagnostics/vif_bar_chart.png`（新增）
- `output/tables/vif_results.csv`
- `output/tables/heteroscedasticity_tests.csv`

---

## 脚本 05 — 模型比较

**状态：** ✅ 已完成

| 模型 | R² | RMSE（元/㎡） | MAE（元/㎡） | AIC |
|------|:---:|:-------------:|:------------:|:---:|
| **OLS + 多项式** | **0.8294** | **9,411** | **6,471** | **-207,770** |
| OLS + 交互项 | 0.8218 | 9,621 | 6,631 | -205,038 |
| OLS（全变量） | 0.8185 | 9,696 | 6,703 | -203,859 |
| Ridge（CV, alpha=0.49） | 0.8185 | 9,696 | 6,703 | — |
| OLS（筛选变量） | 0.8184 | 9,695 | 6,703 | -203,867 |
| LASSO（CV, alpha=1e-4） | 0.8180 | 9,710 | 6,713 | — |

**交叉验证（5折）结果一致**：OLS + 多项式 CV R²=0.8295±0.002，未过拟合。

### DOM 稳健性检验

| 设定 | R² | 说明 |
|------|:---:|------|
| 含 DOM + DOM_missing | 0.8185 | 基准设定 |
| 剔除 DOM 及 DOM_missing | 0.8175 | 差异 0.001 |

核心变量系数对比：
- dist_center：含DOM=-2.689，无DOM=-2.698，差异0.33%
- Lat：含DOM=1.102，无DOM=1.110，差异-0.65%
- Lng：含DOM=-0.507，无DOM=-0.511，差异0.89%
- ladderRatio：含DOM=0.168，无DOM=0.167，差异0.42%
- DOM_missing 系数：-0.028（p=6.7e-165），DOM缺失房源系统性价格偏低

### 已保存输出
- `output/figures/05_comparison/model_comparison.png`
- `output/figures/05_comparison/best_model_coefficients.png`（已修复：改用共识变量 OLS）
- `output/figures/05_comparison/prediction_vs_actual.png`（新增）
- `output/figures/05_comparison/district_coefficients.png`（新增）
- `output/tables/model_comparison.csv`
- `output/tables/cv_comparison.csv`
- `output/tables/dom_robustness.csv`（新增：DOM稳健性检验）

---

## 汇总表

| 脚本 | 关键输出 | 数值 |
|--------|-----------|-------|
| 01 | 数据规模 | ~31.8 万 × 26，2011-2017 |
| 02 | 预处理后特征 | 64（16N + 48D），含时间固定效应 |
| 03 | 共识变量数 | 59 |
| 04 | 是否存在异方差？ | BP p=1.8e-159（拒绝同方差），GQ p=0.857 |
| 04 | 条件数（全变量OLS） | 1.67e+04 |
| 04 | 条件数（多项式模型） | 1.11e+12 |
| 04 | 条件数（交互项模型） | 1.41e+16 |
| 05 | 最优模型 | OLS + 多项式（R²=0.829, RMSE=9,411 元/㎡） |
| 05 | DOM缺失对核心系数影响 | 最大差异<1%，结论稳健 |
