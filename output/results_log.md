# 结果记录

> 各分析脚本的关键数值输出记录。
> 更新日期：2026-04-30（加入时间固定效应后重新运行）

---

## 脚本 01 — 探索性数据分析

**状态：** ✅ 已完成

| 指标 | 数值 |
|--------|-------|
| 交易总条数（过滤后） | ~30 万 |
| 时间跨度 | 2011–2017 |
| 区域数量 | 15 |
| 价格均值 | 43,562 元/㎡ |
| 价格中位数 | 38,752 元/㎡ |
| 价格偏度（原始） | ~1.31 |
| 价格偏度（对数） | ~−0.59 |
| 与价格相关性最高 | communityAverage (0.685), totalPrice (0.660) |

### 已保存图片
- `output/figures/01_eda/price_distribution.png`
- `output/figures/01_eda/correlation_heatmap.png`
- `output/figures/01_eda/geo_price_scatter.png`
- `output/figures/01_eda/price_by_district.png`
- `output/figures/01_eda/price_trend_by_year.png`
- `output/figures/01_eda/price_by_*.png`（6 个分类变量对比）
- `output/figures/01_eda/numeric_distributions.png`
- `output/figures/01_eda/pairplot_key_vars.png`

---

## 脚本 02 — 数据预处理

**状态：** ✅ 已完成（已重新运行）

| 指标 | 数值 |
|--------|-------|
| 训练样本 | 254,528 |
| 测试样本 | 63,632 |
| 特征总数 | 64（16 个数值型 + 48 个虚拟变量） |
| 时间固定效应 | trade_year（2011-2017, 6 个虚拟变量）, trade_month（1-12, 11 个虚拟变量） |
| Winsorize 截尾变量 | price(0.5%), square(0.5%), ladderRatio(1%), followers(1%), DOM(1%) |

### 关键变更说明
- `trade_year` 从连续变量改为年份虚拟变量（2011 为基期），捕捉非线性时间趋势
- `trade_month` 从连续变量改为月份虚拟变量（1 月为基期），控制季节性波动
- 过滤了 404 行 `trade_year` 不在 2011-2017 范围的异常记录

### 已保存数据
- `output/processed_data.pkl` — 未标准化的训练/测试集 + 特征列表
- `output/scaled_data.pkl` — 标准化后的训练/测试集 + 列名
- `output/scaler.pkl` — StandardScaler 对象

---

## 脚本 03 — 变量选择

**状态：** ✅ 已完成（已重新运行）

| 方法 | 选中变量数 |
|--------|-------------------|
| 向前选择（AIC） | 30 |
| 向后剔除（AIC） | 60 |
| LASSO（CV, alpha=0.0001） | 60 |
| 共识（≥2 种方法） | 59 |

**一致性分布：**
- 29 个变量被全部 3 种方法选中
- 30 个变量被 2 种方法选中
- 4 个变量被仅 1 种方法选中
- 1 个变量（`floor_level_δ֪`）未被任何方法选中

> 注意：时间固定效应的加入使特征数从 49 增至 64。年份虚拟变量（尤其是 trade_year_2017）在变量选择中表现出最强的预测信号。

### 共识 OLS（|系数| 前 5）
| 变量 | 系数 | p 值 |
|----------|------------|---------|
| const | 26.916 | 0.000 |
| dist_center | -2.726 | 0.000 |
| trade_year_2017 | 1.172 | 0.000 |
| Lat | 1.110 | 0.000 |
| trade_year_2016 | 0.845 | 0.000 |

### 已保存输出
- `output/selection_results.pkl`
- `output/tables/selection_comparison.csv`
- `output/tables/consensus_ols_coefficients.csv`
- `output/figures/03_selection/lasso_path.png`

---

## 脚本 04 — 模型诊断

**状态：** ✅ 已完成（子样本 2 万行，已重新运行）

| 检验 | 结果 |
|------|--------|
| VIF > 10 变量数 | 9（buildingStructure 系列、square、log_square、部分年份虚拟变量） |
| 最大 VIF（不含常数项） | 492.4（buildingStructure_6） |
| 条件数（Cond. No.） | 4.59e+05（多重共线性较严重，但较原模型 7.84e+06 大幅改善） |
| Breusch-Pagan p 值 | 1.8e-159（拒绝同方差） |
| Goldfeld-Quandt p 值 | 0.857（不拒绝同方差） |
| Durbin-Watson | 1.966（无自相关） |
| Cook's D 异常点（%） | 947（4.74%） |
| HC3 下显著性改变的变量 | 1（fiveYearsProperty_1.0） |
| 测试集 R² | 0.818（对数尺度） |
| 测试集 RMSE | 9,690 元/㎡ |
| 测试集 MAE | 6,704 元/㎡ |

### 条件数改善说明
加入时间固定效应后，条件数从 7.84×10⁶ 降至 4.59×10⁵，降幅约 94%。这是因为年份虚拟变量替代了 trade_year 连续变量后，消除了 trade_year 与其二次项之间的近线性关系。

### 已保存输出
- `output/figures/04_diagnostics/residual_diagnostics.png`
- `output/figures/04_diagnostics/influential_points.png`
- `output/tables/vif_results.csv`
- `output/tables/heteroscedasticity_tests.csv`

---

## 脚本 05 — 模型比较

**状态：** ✅ 已完成（已重新运行）

| 模型 | R² | RMSE（元/㎡） | MAE（元/㎡） | AIC |
|------|:---:|:-------------:|:------------:|:---:|
| **OLS + 多项式** 🏆 | **0.8294** | **9,411** | **6,471** | **-207,770** |
| OLS + 交互项 | 0.8218 | 9,621 | 6,631 | -205,038 |
| OLS（全变量） | 0.8185 | 9,696 | 6,703 | -203,859 |
| Ridge（CV, alpha=0.49） | 0.8185 | 9,696 | 6,703 | — |
| OLS（筛选变量） | 0.8184 | 9,694 | 6,703 | -203,867 |
| LASSO（CV, alpha=1e-4） | 0.8180 | 9,710 | 6,713 | — |

**交叉验证（5折）结果一致**：OLS + 多项式 CV R²=0.8295±0.002，未过拟合。

> 多项式模型在 dist_center、Lat、Lng、ladderRatio、DOM 上增加二次项和交互项（trade_year 因已转为虚拟变量不再参与多项式扩展），共 79 个特征。R² 从 0.818 提升至 0.829，RMSE 降低约 285 元/㎡。

> 与旧模型（连续 trade_year）相比：基准 OLS 的 R² 从 0.786 提升至 0.818（+3.2 pp），RMSE 从 10,428 降至 9,696（-7.0%）。OLS 与多项式模型之间的 R² 差距从 1.9 pp 缩窄至 1.1 pp。

### 已保存输出
- `output/figures/05_comparison/model_comparison.png`
- `output/figures/05_comparison/best_model_coefficients.png`
- `output/tables/model_comparison.csv`
- `output/tables/cv_comparison.csv`

---

## 汇总表

| 脚本 | 关键输出 | 数值 |
|--------|-----------|-------|
| 01 | 数据规模 | ~30 万 × 26 |
| 02 | 预处理后特征 | 64（16N + 48D），含时间固定效应 |
| 03 | 共识变量数 | 59 |
| 04 | 是否存在异方差？ | BP p=1.8e-159（拒绝同方差），GQ p=0.857 |
| 04 | 条件数 | 4.59e+05（原 7.84e+06，改善 94%） |
| 05 | 最优模型 | OLS + 多项式（R²=0.829, RMSE=9,411 元/㎡） |
