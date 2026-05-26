"""
北京住房价格回归分析 —— 共享工具模块

集中管理路径、绘图配置、导出工具等通用功能。
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.colors as mcolors
import pandas as pd
import numpy as np

# ── 项目路径 ──
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"

# ── 配色方案（学术蓝橙，Nature 子刊风格）──
CB_PALETTE = ["#4DBBD5", "#F39B7F", "#00A087", "#91D1C2", "#8491B4", "#FCC5A1"]

# ── 自定义 colormap ──
# 发散色图：蓝-白-红，用于相关性热力图等
DIVERGING_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "academic_diverging",
    ["#4DBBD5", "#F7F7F7", "#F39B7F"],
)

# 顺序色图：浅橙-深绿，用于地理散点等连续值映射
SEQUENTIAL_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "academic_sequential",
    ["#FCC5A1", "#F39B7F", "#4DBBD5", "#00A087"],
)


def setup_font():
    """配置中文字体和全局绘图参数，确保所有脚本风格一致。"""
    candidates = [
        "SimHei",
        "Microsoft YaHei",
        "PingFang SC",
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
        "DejaVu Sans",
    ]
    for font in candidates:
        try:
            matplotlib.font_manager.findfont(font, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
            break
        except Exception:
            continue

    plt.rcParams.update({
        "axes.unicode_minus": False,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })


# ── 辅助函数 ──

def load_data(nrows=None, encoding="gbk"):
    """加载链家北京二手房数据集。"""
    path = DATA_DIR / "lianjia_beijing.csv"
    df = pd.read_csv(path, encoding=encoding, nrows=nrows, low_memory=False)
    print(f"加载 {len(df):,} 行 x {len(df.columns)} 列")
    return df


def print_section(title: str):
    """打印分段标题。"""
    line = "=" * 70
    print(f"\n{line}\n{title}\n{line}")


def save_fig(name: str, subdir: str = ""):
    """保存当前 matplotlib 图为 PNG 并关闭。"""
    path = FIGURES_DIR / subdir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  [保存] {path}")


def save_table(df: pd.DataFrame, name: str):
    """将 DataFrame 保存为 CSV 到 tables 目录。"""
    path = TABLES_DIR / name
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"  [保存] {path}")
