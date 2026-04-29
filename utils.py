"""
北京住房价格回归分析 —— 共享工具模块

集中管理路径、绘图配置、导出工具等通用功能。
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import numpy as np

# ── 项目路径 ──
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
OUTPUT_DIR = PROJECT_ROOT / "output"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"

# ── Matplotlib 全局配置 ──
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.figsize": (10, 6),
    "axes.unicode_minus": False,
})
_attempted_font = False


def setup_font():
    """配置中文字体，确保图表能正常显示中文标签。"""
    global _attempted_font
    if _attempted_font:
        return
    _attempted_font = True
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


# ── 配色方案（色盲友好）──
CB_PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]


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
