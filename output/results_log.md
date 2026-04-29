# 结果记录

> 各分析脚本的关键数值输出记录。
> 首次运行脚本后更新此文件。

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

**状态：** ✅ 已完成

| 指标 | 数值 |
|--------|-------|
| 训练样本 | 254,851 |
| 测试样本 | 63,713 |
| 特征总数 | 49（18 个数值型 + 31 个虚拟变量） |
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
| 向后剔除（AIC） | 44 |
| LASSO（CV, alpha=0.0001） | 46 |
| 共识（≥2 种方法） | 44 |

**一致性分布：**
- 28 个变量被全部 3 种方法选中
- 16 个变量被 2 种方法选中
- 4 个变量被仅 1 种方法选中
- 1 个变量（`floor_level_δ֪`）未被任何方法选中

> 注意：LASSO 最优 alpha（0.0001）命中了搜索网格 [10⁻⁴, 10⁰] 的下界。模型仍然保留了 46/49 个变量，说明惩罚较弱，结果接近 OLS 而非稀疏模型。将网格向下扩展会产生相同的结果。

### 共识 OLS（|系数| 前 5）
| 变量 | 系数 | p 值 |
|----------|------------|---------|
| const | -338.85 | 0.000 |
| dist_center | -2.681 | 0.000 |
| Lat | 1.089 | 0.000 |
| district_6 | -0.502 | 0.000 |
| Lng | -0.488 | 0.000 |

### 已保存输出
- `output/selection_results.pkl`
- `output/tables/selection_comparison.csv`
- `output/tables/consensus_ols_coefficients.csv`
- `output/figures/03_selection/lasso_path.png`

---

## 脚本 04 — 模型诊断

**状态：** ✅ 已完成（子样本 2 万行）

| 检验 | 结果 |
|------|--------|
| VIF > 10 变量数 | 6（buildingStructure 系列、square、log_square） |
| 最大 VIF（不含常数项） | 358.2（buildingStructure_6） |
| 条件数（Cond. No.） | 7.84e+06（可能存在严重多重共线性） |
| Breusch-Pagan p 值 | 3.55e-141（拒绝同方差） |
| Goldfeld-Quandt p 值 | 0.159（不拒绝同方差） |
| Durbin-Watson | 1.969（无自相关） |
| Cook's D 异常点（%） | 978（4.89%） |
| HC3 下显著性改变的变量 | 3（buildingStructure_2, _4, _5） |
| 测试集 R² | 0.785（对数尺度） |
| 测试集 RMSE | 10,416 元/㎡ |
| 测试集 MAE | 7,363 元/㎡ |

### 已保存输出
- `output/figures/04_diagnostics/residual_diagnostics.png`
- `output/figures/04_diagnostics/influential_points.png`
- `output/tables/vif_results.csv`
- `output/tables/heteroscedasticity_tests.csv`

---

## 脚本 05 — 模型比较

**状态：** ✅ 已完成

| 模型 | R² | RMSE（元/㎡） | MAE（元/㎡） | AIC |
|------|:---:|:-------------:|:------------:|:---:|
| **OLS + 多项式** 🏆 | **0.8047** | **9,874** | **6,947** | **-199,192** |
| OLS + 交互项 | 0.7899 | 10,372 | 7,295 | -194,550 |
| OLS（全变量） | 0.7859 | 10,428 | 7,361 | -193,391 |
| Ridge（CV, alpha=2.02） | 0.7859 | 10,428 | 7,361 | — |
| OLS（筛选变量） | 0.7859 | 10,425 | 7,363 | -193,390 |
| LASSO（CV, alpha=1e-4） | 0.7858 | 10,429 | 7,367 | — |

**交叉验证（5折）结果一致**：OLS + 多项式 CV R²=0.8042±0.002，未过拟合。

> 多项式模型在 dist_center、Lat、Lng、trade_year、ladderRatio、DOM 上增加二次项和交互项，共 70 个特征。R² 从 0.786 提升至 0.805，RMSE 降低约 554 元/㎡。

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
| 02 | 预处理后特征 | 49（18N + 31D） |
| 03 | 共识变量数 | 44 |
| 04 | 是否存在异方差？ | BP p=3.55e-141（拒绝同方差），GQ p=0.159 |
| 05 | 最优模型 | OLS + 多项式（R²=0.805, RMSE=9,874 元/㎡） |
