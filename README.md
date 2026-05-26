# 北京市住房价格影响因素分析

基于链家 2011–2017 年北京二手房成交数据（约 30 万条），运用多元回归分析方法探究住房价格的影响因素。项目涵盖**数据预处理 → 探索性分析 → 变量选择 → 模型诊断 → 多模型比较**的完整回归分析流程。

## 数据说明

数据来源为链家北京二手房成交记录，原始 26 个字段，经预处理后最终特征空间包含 **64 个特征**（16 个数值型 + 48 个虚拟变量），其中时间固定效应由 6 个年度虚拟变量和 11 个月度虚拟变量构成。

## 分析流程

```
01_exploratory.py         探索性数据分析（分布、相关性、地理分布、时间趋势）
        ↓
02_preprocessing.py       数据预处理（清洗、插补、Winsorize、特征工程、独热编码）
        ↓
03_variable_selection.py  变量选择（向前选择AIC + 向后剔除AIC + LASSO）→ 共识变量集59个
        ↓
04_model_diagnostics.py   模型诊断（VIF、异方差BP/GQ、自相关DW、Cook's D、HC3稳健标准误）
        ↓
05_model_comparison.py    多模型比较（6种模型 × 测试集评估 × 5折交叉验证）+ DOM稳健性检验
```

## 模型比较结果

| 模型 | R² | RMSE（元/㎡） |
|------|:---:|:-------------:|
| **OLS + 多项式** | **0.8294** | **9,411** |
| OLS + 交互项 | 0.8218 | 9,621 |
| OLS（全变量） | 0.8185 | 9,696 |
| Ridge（CV） | 0.8185 | 9,696 |
| OLS（筛选变量） | 0.8184 | 9,695 |
| LASSO（CV） | 0.8180 | 9,710 |

多项式模型预测精度最高，但高阶项导致系数膨胀至无法经济解释（条件数 1.11×10¹²）。综合预测精度与可解释性，推荐带时间-区域双向固定效应的线性主效应模型。

## 文件结构

```
├── scripts/               # 分析脚本（按流程编号）
├── data/                  # 原始数据
├── output/                # 输出结果
│   ├── figures/           # 可视化图表（按脚本分目录）
│   ├── tables/            # 数值结果表格（CSV）
│   └── results_log.md     # 关键数值结果记录
├── report/                # 论文
│   ├── paper.tex          # LaTeX 论文源文件
│   ├── paper.pdf          # 编译输出
│   └── build.bat          # 编译脚本（xelatex × 2）
├── utils.py               # 共享工具函数
└── CLAUDE.md              # 项目配置
```

## 运行方式

```bash
python scripts/01_exploratory.py
python scripts/02_preprocessing.py
python scripts/03_variable_selection.py    # 耗时较长
python scripts/04_model_diagnostics.py     # 耗时较长
python scripts/05_model_comparison.py      # 耗时较长
```

## 编译论文

```bash
cd report && build.bat
# 或手动执行两次 xelatex 以解析交叉引用
```

## 依赖

- Python ≥ 3.10：pandas, numpy, scipy, matplotlib, seaborn, statsmodels, scikit-learn, joblib
- LaTeX：TeX Live + XeLaTeX（中文支持）
