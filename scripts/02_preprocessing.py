"""
脚本 2：数据预处理
====================
目标：清洗、变换、准备好建模数据。
输出处理后的数据集（pickle 文件）。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats.mstats import winsorize
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
from utils import (
    setup_font, load_data, print_section, save_fig, save_table, CB_PALETTE
)

setup_font()

SEED = 42

# ── 1. 加载原始数据 ──
print_section("1. 加载原始数据")
df = load_data()
print(f"原始形状：{df.shape}")

# ── 2. 删除有问题的列 ──
print_section("2. 删除有问题的列")

# communityAverage：社区均价，与目标变量高度相关——数据泄露
# totalPrice：总价 = 单价 × 面积，是目标的确定性函数
# Cid：社区 ID，超 6000 个类别，无法泛化
# url, id：标识符，无预测价值
drop_cols = ["communityAverage", "totalPrice", "Cid", "url", "id"]
df.drop(columns=drop_cols, inplace=True)
print(f"已删除：{drop_cols}")
print(f"删除后形状：{df.shape}")

# ── 3. 修正数据类型 ──
print_section("3. 修正数据类型")

# 这些列本应是数值，但可能混入文本
for col in ["livingRoom", "drawingRoom", "bathRoom", "constructionTime", "DOM"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    print(f"  {col}: {df[col].dtype}，{df[col].isna().sum()} 个被强制转为 NaN")

# ── 4. 过滤极端/不可能的值 ──
print_section("4. 过滤极端值")

n_before = len(df)
# 再次确保价格合理
df = df[df["price"] > 100].copy()
# 建造年份合理范围（1920-2017）
df = df[(df["constructionTime"].isna()) | (df["constructionTime"] >= 1920) &
        (df["constructionTime"] <= 2017)]
# 卫生间数量合理（0-10，原始数据中有 2011 这样的错误值）
df = df[(df["bathRoom"].isna()) | (df["bathRoom"] <= 10)]
# 客厅数量合理
df = df[(df["livingRoom"].isna()) | (df["livingRoom"] <= 15)]
# 餐厅数量合理
df = df[(df["drawingRoom"].isna()) | (df["drawingRoom"] <= 10)]
# 面积合理（10-1000 平米）
df = df[(df["square"] >= 10) & (df["square"] <= 1000)]
n_removed = n_before - len(df)
print(f"删除了 {n_removed} 行极端值，当前形状：{df.shape}")

# ── 5. 处理缺失值 ──
print_section("5. 处理缺失值")

missing_before = df.isnull().sum()
print("插补前的缺失情况：")
print(missing_before[missing_before > 0].to_string())

# DOM：50% 缺失——用中位数填充 + 添加缺失标记
df["DOM_missing"] = df["DOM"].isna().astype(int)
df["DOM"].fillna(df["DOM"].median(), inplace=True)

# constructionTime：约 6% 缺失——中位数填充
df["constructionTime"].fillna(df["constructionTime"].median(), inplace=True)

# 分类变量：众数填充
cat_impute = ["buildingType", "elevator", "fiveYearsProperty", "subway"]
for col in cat_impute:
    df[col].fillna(df[col].mode()[0], inplace=True)

# livingRoom, drawingRoom, bathRoom：中位数填充（之前 coerced 到 NaN 的用中位数补）
for col in ["livingRoom", "drawingRoom", "bathRoom"]:
    df[col].fillna(df[col].median(), inplace=True)

# ladderRatio：无缺失，但有极端值——在下一步处理
# communityAverage 已删除

missing_after = df.isnull().sum()
print("\n插补后的缺失情况：")
print(missing_after[missing_after > 0].to_string() if missing_after.sum() > 0 else "  无缺失！")

# ── 6. 异常值处理（Winsorize 截尾）──
print_section("6. 异常值处理（Winsorize 截尾）")

winsorize_cols = {
    "price": (0.005, 0.005),          # 两侧各 0.5%
    "square": (0.005, 0.005),
    "ladderRatio": (0.01, 0.01),      # 两侧各 1%（原始数据有上千万的极端值）
    "followers": (0.01, 0.01),
    "DOM": (0.01, 0.01),
}

for col, (lower, upper) in winsorize_cols.items():
    original_std = df[col].std()
    df[col] = winsorize(df[col], limits=(lower, upper))
    new_std = df[col].std()
    print(f"  {col}: 标准差 {original_std:.1f} -> {new_std:.1f}")

# ── 7. 解析楼层变量 ──
print_section("7. 解析楼层变量")

def parse_floor(s):
    """解析楼层字符串如 'high 26'，拆分为楼层类别和楼层数。"""
    s = str(s)
    parts = s.split()
    if len(parts) == 0:
        return None, None
    level = parts[0]
    num = parts[1] if len(parts) > 1 else None
    # 映射中文楼层代号
    level_map = {"低": "low", "中": "mid", "高": "high", "地": "ground"}
    level = level_map.get(level, level)
    return level, num

floor_data = df["floor"].apply(parse_floor)
df["floor_level"] = floor_data.apply(lambda x: x[0])
df["floor_num"] = pd.to_numeric(floor_data.apply(lambda x: x[1]), errors="coerce")
df["floor_num"].fillna(df["floor_num"].median(), inplace=True)

print(f"  楼层类别分布：\n{df['floor_level'].value_counts().to_string()}")

# ── 8. 创建衍生变量 ──
print_section("8. 创建衍生变量")

# 成交时间转日期格式
df["tradeTime"] = pd.to_datetime(df["tradeTime"], errors="coerce")
df["trade_year"] = df["tradeTime"].dt.year
df["trade_month"] = df["tradeTime"].dt.month

# 房龄（交易时）
df["property_age"] = df["trade_year"] - df["constructionTime"]
df["property_age"] = df["property_age"].clip(lower=0, upper=100)

# 距北京市中心（天安门附近）距离
beijing_center = (116.3974, 39.9082)
df["dist_center"] = np.sqrt(
    (df["Lng"] - beijing_center[0]) ** 2 +
    (df["Lat"] - beijing_center[1]) ** 2
)

# 对数变换目标变量
df["log_price"] = np.log(df["price"])

# 对数变换重尾分布的自变量
df["log_square"] = np.log(df["square"])
df["log_followers"] = np.log1p(df["followers"])

# 过滤交易年份：仅保留 2011-2017（数据已知范围）
n_before_year = len(df)
df = df[df["trade_year"].between(2011, 2017)].copy()
print(f"  过滤交易年份：{n_before_year - len(df)} 行被删除（不在 2011-2017 范围内）")

print("  已创建：trade_year, trade_month, property_age, dist_center, log_price, log_square, log_followers")

# ── 9. 编码分类变量 ──
print_section("9. 编码分类变量")

cat_cols = {
    "buildingType": "category",
    "buildingStructure": "category",
    "renovationCondition": "category",
    "elevator": "category",
    "subway": "category",
    "fiveYearsProperty": "category",
    "floor_level": "category",
    "district": "category",
    "trade_year": "category",
    "trade_month": "category",
}

for col, dtype in cat_cols.items():
    df[col] = df[col].astype(dtype)

# 独热编码（drop_first 避免虚拟变量陷阱）
df_encoded = pd.get_dummies(df, columns=list(cat_cols.keys()), drop_first=True, dtype=int)

print(f"编码后形状：{df_encoded.shape}")

# ── 10. 定义特征和标签 ──
print_section("10. 定义特征矩阵和标签")

target = "log_price"
# 不纳入特征的变量
exclude = [
    "log_price", "price", "tradeTime", "constructionTime",
    "floor",  # 原始楼层字符串（已用 floor_level 和 floor_num 代替）
]
feature_cols = [c for c in df_encoded.columns if c not in exclude]
# 仅保留数值型列
feature_cols = [c for c in feature_cols if df_encoded[c].dtype in [np.float64, np.int64, int, np.int32, np.float32]]

X = df_encoded[feature_cols]
y = df_encoded[target]

print(f"特征矩阵：{X.shape}")
print(f"目标变量：{target}")
print(f"特征列表（{len(feature_cols)} 个）：")
for i, c in enumerate(feature_cols):
    print(f"  {i+1:3d}. {c}")

# ── 11. 训练-测试集划分 ──
print_section("11. 训练-测试集划分")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=SEED
)
print(f"训练集：{X_train.shape[0]:,} 行")
print(f"测试集：{X_test.shape[0]:,} 行")

# ── 12. 标准化（用于正则化模型）──
print_section("12. 标准化（用于正则化模型）")

# 识别虚拟变量列（不进行标准化）
dummy_patterns = [
    "buildingType_", "buildingStructure_", "renovationCondition_",
    "elevator_", "subway_", "fiveYearsProperty_", "floor_level_", "district_",
    "trade_year_", "trade_month_"
]
dummy_cols = [c for c in feature_cols if any(p in c for p in dummy_patterns)]
numeric_cols = [c for c in feature_cols if c not in dummy_cols]

print(f"数值型（已标准化）：{len(numeric_cols)}")
print(f"虚拟变量（未标准化）：{len(dummy_cols)}")

scaler = StandardScaler()
X_train_scaled = X_train.copy()
X_test_scaled = X_test.copy()

X_train_scaled[numeric_cols] = scaler.fit_transform(X_train[numeric_cols])
X_test_scaled[numeric_cols] = scaler.transform(X_test[numeric_cols])

print("标准化完成。")

# ── 13. 保存处理后的数据 ──
print_section("13. 保存处理结果")

joblib.dump((X_train, X_test, y_train, y_test, feature_cols),
             "output/processed_data.pkl")
joblib.dump((X_train_scaled, X_test_scaled, numeric_cols, dummy_cols),
             "output/scaled_data.pkl")
joblib.dump(scaler, "output/scaler.pkl")

print("已保存：")
print("  output/processed_data.pkl  （未标准化的训练/测试集）")
print("  output/scaled_data.pkl     （标准化后的训练/测试集 + 列名）")
print("  output/scaler.pkl          （StandardScaler 对象）")

# ── 14. 关键数值结果 ──
print_section("14. 关键数值结果")
print(f"""
最终：{X_train.shape[0]:,} 训练 / {X_test.shape[0]:,} 测试，{len(feature_cols)} 个特征（{len(numeric_cols)} 个数值型 + {len(dummy_cols)} 个虚拟变量）
已删除 {n_removed} 行极端值，插补 {missing_before.sum()} 个缺失值
Winsorize 截尾：price(0.5%), square(0.5%), ladderRatio(1%), followers(1%), DOM(1%)
""")

print("脚本 02 完成。")
