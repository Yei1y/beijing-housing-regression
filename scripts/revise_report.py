"""
脚本：大修分析报告.docx
========================
基于时间固定效应新结果，按教授指导意见大修报告。
更新数值、重写关键章节、修复逻辑断层。
"""

import sys
from docx import Document
from docx.shared import Pt, RGBColor
import re


def para_startswith(para, prefix):
    """检查段落是否以指定文本开头（忽略空格差异）"""
    return para.text.strip().startswith(prefix)


def replace_para_text(doc, idx, new_text):
    """替换段落文本，保留原有格式"""
    para = doc.paragraphs[idx]
    # 清除所有 run
    for run in para.runs:
        run.text = ""
    # 在第一个 run 中写入新文本
    if para.runs:
        para.runs[0].text = new_text
    else:
        para.add_run(new_text)


def find_para_by_prefix(doc, prefix, start=0):
    """查找以指定前缀开头的段落索引"""
    for i, para in enumerate(doc.paragraphs):
        if i < start:
            continue
        if para_startswith(para, prefix):
            return i
    return None


def clear_table_cell(table, row, col):
    """清空表格单元格"""
    cell = table.cell(row, col)
    for p in cell.paragraphs:
        for run in p.runs:
            run.text = ""
        if p.runs:
            p.runs[0].text = ""


def set_cell_text(table, row, col, text):
    """设置表格单元格文本（彻底清空后写入）"""
    cell = table.cell(row, col)
    # 清除所有段落的所有 run
    for p in cell.paragraphs:
        for run in p.runs:
            run.text = ""
    # 也清除 XML 中的直接文本节点
    for p in cell.paragraphs:
        p.clear()
    # 写入新文本
    p = cell.paragraphs[0]
    p.add_run(text)


def main():
    doc = Document("report/分析报告.docx")
    paras = doc.paragraphs

    # ===== 1. 更新摘要 =====
    print("更新摘要...")
    p = paras[12]
    old_text = p.text
    if "0.805" in old_text:
        new_text = old_text.replace("（R²=0.805，RMSE=9874元/㎡）", "（R²=0.829，RMSE=9411元/㎡）")
        new_text = new_text.replace("0.786", "0.818")
        new_text = new_text.replace("R²=0.805", "R²=0.829")
        # 更新条件数引用
        new_text = new_text.replace("7.84", "4.59")
        new_text = new_text.replace("6个区域的虚拟变量", "时间固定效应（年度和月度虚拟变量）和15个区域虚拟变量")
        # 更新HC3改变变量数
        new_text = new_text.replace("3个变量的显著性判断发生改变", "1个变量的显著性判断发生改变")
        replace_para_text(doc, 12, new_text)
        print("  摘要已更新")

    # ===== 2. 重写 2.3 模型设定 =====
    print("重写 2.3 模型设定...")
    # 段落 [33]-[41] 要被替换

    # 段 [33]: "本研究以特征价格模型为理论基础..."
    p33_new = "本研究在特征价格模型框架下，设定包含时间和区域双向固定效应的半对数回归方程作为基准模型："
    replace_para_text(doc, 33, p33_new)

    # 段 [34]: 旧公式 → 新公式
    p34_new = (
        "log(Price_{it}) = β₀ + X_{it}′β + γ_t + δ_k + ε_{it}"
    )
    replace_para_text(doc, 34, p34_new)

    # 段 [35]: 解释
    p35_new = (
        "其中 log(Price_{it}) 为第 i 条交易在第 t 期的对数价格；"
        "X_{it} 包含连续型房屋和区位特征（dist_center、Lat、Lng、square、log_square、ladderRatio、DOM 等）；"
        "γ_t 为时间固定效应，以年度虚拟变量（trade_year_2012 至 trade_year_2017，2011 年为基期）"
        "和月度虚拟变量（trade_month_2 至 trade_month_12，1 月为基期）实现，"
        "灵活捕捉非线性的时间趋势和季节性波动；"
        "δ_k 为区域固定效应（district_* 虚拟变量），控制不随时间变化的区域异质性。"
        "该设定的优势在于不施加「年度价格增幅恒定」的线性约束，"
        "允许数据自行估计每年的基准价格水平。"
        "ε_{it} 为随机误差项。"
    )
    replace_para_text(doc, 35, p35_new)

    # 段 [36]: 原来的"进一步引入" → 改为简洁过渡
    p36_new = (
        "双向固定效应的引入消解了原模型中 trade_year 作为连续变量的设定偏误。"
        "在 EDA 部分（3.4 节）将展示：2011-2017 年房价趋势呈明显非线性特征，"
        "因此 γ_t 的灵活设定比线性 trade_year 更为合理。"
    )
    replace_para_text(doc, 36, p36_new)

    # 段 [37]: 原来的第二个公式 → 改为多项式扩展说明
    p37_new = (
        "为探索空间和房屋属性变量的非线性边际效应，对 5 个关键连续变量构造多项式扩展模型："
    )
    replace_para_text(doc, 37, p37_new)

    # 段 [38]: 原来的"值得注意的是" → 改为多项式公式说明
    p38_new = (
        "log(Price) = β₀ + X′β + Z′γ + vec(Z ⊗ Z)′θ + ε"
    )
    replace_para_text(doc, 38, p38_new)

    # 段 [39]: 旧6个关键变量 → 改为5个
    p39_new = (
        "其中 Z 为 5 个关键连续变量（dist_center、Lat、Lng、ladderRatio、DOM）组成的向量。"
        "经度和纬度参与扩展以捕捉空间曲面的弯曲，"
        "梯户比和挂牌天数参与扩展以允许边际效应递减。"
        "trade_year 不再参与多项式扩展——因为时间固定效应已通过年度虚拟变量灵活捕捉了非线性的时间趋势。"
        "Z ⊗ Z 包含所有二次项和两两交互项。"
        "该设定允许关键变量存在非线性边际效应，但代价是引入严重的多重共线性（见第五章）。"
    )
    replace_para_text(doc, 39, p39_new)

    # 段 [40]: 原第二个多项式公式 → 合并到前一段
    replace_para_text(doc, 40, "")

    # 段 [41]: 原Z的解释 → 改为过渡
    p41_new = (
        "上述线性基准模型（带有时间-区域双向固定效应）是本文进行经济推断的主要依据，"
        "而多项式模型主要用于对比和展示非线性扩展的代价。"
    )
    replace_para_text(doc, 41, p41_new)

    # ===== 3. 增强 2.4 数据预处理 =====
    print("增强 2.4 数据预处理...")

    # 段 [44]: 剔除数据泄露 → 补充对数变换理由
    p44_new = (
        "剔除数据泄露变量：communityAverage（社区均价，与目标变量高度相关会造成前向偏差）、"
        "totalPrice（总价=单价×面积，确定性函数）、Cid（社区 ID，超 6000 个类别），以及标识符变量（url, id）。"
    )
    replace_para_text(doc, 44, p44_new)

    # 段 [46]: 极端值过滤 → 补充说明
    p46_new = (
        "极端值过滤：剔除价格<100元/㎡、面积<10㎡或>1000㎡、卫生间>10等不合理记录，"
        "共删除约300行（新数据经更严格的时间范围过滤后总量略有调整）。"
    )
    replace_para_text(doc, 46, p46_new)

    # 段 [48]: 异常值截尾 → 补充 Winsorize 理由
    p48_new = (
        "异常值截尾：对 price、square、ladderRatio、followers、DOM 共 5 个变量进行 Winsorize 截尾处理"
        "（price 和 square 为 0.5%，其余为 1%），将极端值替换为分位数值而非直接删除。"
        "保留样本量同时削弱极端值对 OLS 系数的过度影响。"
        "对于 ladderRatio（原始数据中存在千万级异常值）等变量尤为重要。"
    )
    replace_para_text(doc, 48, p48_new)

    # 段 [49]: 衍生变量构造 → 补充时间固定效应相关
    p49_new = (
        "衍生变量构造：创建 property_age（交易年份-建造年份）、dist_center（距天安门经纬度的欧氏距离）、"
        "trade_year 和 trade_month（从交易时间提取，并在后续作为分类变量进行独热编码以构建时间固定效应）、"
        "log_square 和 log_followers（对数变换）、floor_level（楼层类别，如高/中/低/底/顶/未知）。"
    )
    replace_para_text(doc, 49, p49_new)

    # 段 [50]: 对数变换 → 详细说明统计理由
    p50_new = (
        "对数变换目标变量：对 price 取自然对数作为回归目标。"
        "理由有三：（1）缓解右偏——原始价格偏度约 1.31，对数变换后降至约 -0.59，分布更接近对称，"
        "有助于满足 OLS 残差近似正态性的假设；（2）稳定方差——房价波动随价格水平增加，"
        "对数变换将绝对差异转化为相对差异，缓解异方差；"
        "（3）经济学解释——对数线性模型中系数 ×100 近似解释为半弹性（semi-elasticity），"
        "比原始尺度的「每增加一单位价格变化多少元」更便于跨变量比较。"
    )
    replace_para_text(doc, 50, p50_new)

    # 段 [51]: 独热编码 → 更新特征数量
    p51_new = (
        "独热编码：对 10 个分类变量（buildingType、buildingStructure、renovationCondition、elevator、"
        "subway、fiveYearsProperty、floor_level、district、trade_year、trade_month）"
        "进行 one-hot 编码（drop_first=True），最终得到 64 个特征（16 个数值型 + 48 个虚拟变量）。"
        "其中 trade_year（2011-2017 共 7 年）生成 6 个年度虚拟变量（以 2011 年为基期），"
        "trade_month（1-12 月）生成 11 个月度虚拟变量（以 1 月为基期），共同构成时间固定效应。"
    )
    replace_para_text(doc, 51, p51_new)

    # ===== 4. 更新 2.4.1 DOM 缺失值讨论 =====
    print("更新 2.4.1 DOM 缺失值讨论...")
    # 段 [53-54]
    p53_new = (
        "DOM（挂牌天数）缺失率达 50%，是本数据集中最严重的缺失值问题。"
        "根据 Little & Rubin（2019）的分类框架，完全随机缺失（MCAR）的假设难以成立——"
        "挂牌天数极短的房源可能因系统记录延迟导致 DOM 缺失，更接近于非随机缺失（MNAR）情景。"
        "本研究采用中位数填充 + 缺失指示变量（DOM_missing）的复合策略："
        "中位数填充保留样本量，DOM_missing 吸收缺失机制对截距的系统性偏移。"
    )
    replace_para_text(doc, 53, p53_new)

    p54_new = (
        "回归结果显示，DOM_missing 的系数显著为负（约 -0.028，p < 0.001），"
        "表明 DOM 缺失的房源确实系统性地价格偏低——这一结果与 MNAR 的推论一致"
        "（快速成交房源的定价往往更合理，DOM 缺失机制与价格水平存在关联）。"
        "为检验 DOM 处理对核心结论的敏感性，本文建议：在模型中分别估计"
        "（a）包含 DOM + DOM_missing、（b）完全剔除 DOM 及其指示变量、"
        "（c）仅使用 DOM_missing 三种设定，考察核心变量（dist_center、subway、elevator）"
        "的系数是否发生显著改变。若系数稳定，则表明 DOM 缺失对核心结论不构成实质性威胁。"
    )
    replace_para_text(doc, 54, p54_new)

    # ===== 5. 更新 2.4.2 共线性预设 =====
    print("更新 2.4.2 共线性预设考虑...")
    p56_new = (
        "预处理阶段已注意到共线性来源。其一，square 与 livingRoom 的皮尔逊相关系数高达 0.72，"
        "表明面积与居室数量之间存在高度重叠信息。其二，buildingStructure 系列虚拟变量在独热编码后"
        "呈现类别分布不均衡（某些结构类型的观测极少），导致方差膨胀（后文 VIF 诊断确认）。"
        "时间固定效应（年度和月度虚拟变量）加入后，特征空间从 49 增至 64 个，"
        "但条件数从 7.84×10⁶ 降至 4.59×10⁵，说明原模型的病态程度在教育水平的改善程度上被缓解了。"
    )
    replace_para_text(doc, 56, p56_new)

    # ===== 6. 更新 2.5 数据划分 =====
    print("更新 2.5 数据划分...")
    p58_new = (
        "将数据按 80/20 比例随机划分为训练集（254,528 条）和测试集（63,632 条）。"
        "数值型特征经 StandardScaler 标准化（均值为 0、标准差为 1），"
        "虚拟变量不进行标准化以保持类别间的可比性。标准化后的数据专门用于 Ridge 和 LASSO 正则化模型。"
        "最终特征空间包含 16 个数值型变量和 48 个虚拟变量（含时间固定效应），共计 64 个特征。"
    )
    replace_para_text(doc, 58, p58_new)

    # ===== 7. 更新 3.4 价格时间趋势 =====
    print("更新 3.4 价格时间趋势...")
    p78_new = (
        "这一发现的计量含义十分重要：早期版本的模型中，trade_year 被作为连续线性变量纳入回归，"
        "实质上施加了「年度价格增幅恒定」的约束，这显然不符合数据特征。"
        "在本文的最终模型设定中，trade_year 已被替换为年份虚拟变量（即时间固定效应，"
        "同时纳入月度虚拟变量控制季节性），让数据自行估计每年的基准价格水平。"
        "后文表 X 显示，年份虚拟变量的系数从 2012 年的约 +0.15 逐渐递增至 2017 年的约 +1.15，"
        "年与年之间的增幅并不相等——2015 年后的系数跳跃明显更大，与 EDA 观察到的趋势转折完全一致。"
        "这验证了时间固定效应设定的合理性。"
    )
    replace_para_text(doc, 78, p78_new)

    # ===== 8. 更新 四、变量选择 =====
    print("更新 四、变量选择...")
    p81_new = (
        "为在高维特征空间（64 个特征，含时间固定效应）中识别最重要的预测变量，"
        "本研究综合运用三种方法：基于 AIC 的向前选择、基于 AIC 的向后剔除，以及 LASSO 正则化路径。"
        "采用共识策略（至少被 2 种方法选中）确定最终变量集，以增强变量选择的稳健性。"
    )
    replace_para_text(doc, 81, p81_new)

    p82_new = (
        "变量选择结果如下：全部 64 个特征中，29 个被 3 种方法一致选中（高度稳健），"
        "30 个被 2 种方法选中（中度稳健），4 个仅被 1 种方法选中，1 个未被任何方法选中。"
        "最终共识变量集包含 59 个变量。"
    )
    replace_para_text(doc, 82, p82_new)

    p83_new = (
        "三种方法的一致性程度较高（29 个变量获全票通过）。"
        "被一致选中的重要变量包括：经纬度（Lng, Lat）、距市中心距离（dist_center）、"
        "梯户比（ladderRatio）、有无电梯（elevator）、临近地铁（subway）、"
        "建筑面积对数（log_square）及大部分区域虚拟变量。"
        "值得注意的是，年份虚拟变量（trade_year_2012 至 trade_year_2017）和多数月份虚拟变量也被全票选中，"
        "验证了时间固定效应纳入模型的必要性。"
    )
    replace_para_text(doc, 83, p83_new)

    # [87] LASSO 正则化
    p87_new = (
        "LASSO 交叉验证选择的最优惩罚参数为 alpha=0.0001，恰好位于搜索网格 [10⁻⁴, 10⁰] 的下界。"
        "模型在此参数下保留了 60/64 个非零系数（仅 4 个系数被压缩至零），惩罚力度极为微弱。"
        "将搜索网格向下扩展至 10⁻⁵ 后，最优 alpha 仍然落在新的下界，"
        "表明这一结果并非网格设定问题所导致。"
    )
    replace_para_text(doc, 87, p87_new)

    p88_new = (
        "这一现象的数据解释是：64 个候选特征中绝大多数都与房价存在统计上显著的关联，"
        "强预测信号在特征空间中广泛分布，LASSO 无法通过 L1 惩罚将有效信号压缩为零。"
        "这与「真实模型稀疏」的隐含前提相悖——住房价格通常受众多微效因素共同影响。"
        "因此 LASSO 在本应用中本质上退化为了普通 OLS，"
        "这也解释了为何在后文的模型比较中二者的预测表现几乎完全一致（R² 均为 0.818）。"
    )
    replace_para_text(doc, 88, p88_new)

    # ===== 9. 更新 五、模型诊断表格和正文 =====
    print("更新 五、模型诊断...")

    # 更新诊断表格（Table 1）
    tbl = doc.tables[1]
    set_cell_text(tbl, 1, 0, "VIF > 10 变量数")
    set_cell_text(tbl, 1, 1, "9个（buildingStructure系列、square、log_square、trade_year_2016/2015/2017）")
    set_cell_text(tbl, 2, 0, "最大 VIF（不含常数项）")
    set_cell_text(tbl, 2, 1, "492.4（buildingStructure_6）")
    set_cell_text(tbl, 3, 0, "条件数（Cond. No.）")
    set_cell_text(tbl, 3, 1, "4.59×10⁵（较原模型 7.84×10⁶ 大幅改善）")
    set_cell_text(tbl, 4, 0, "Breusch-Pagan 检验")
    set_cell_text(tbl, 4, 1, "LM=957.6, p=1.8×10⁻¹⁵⁹ → 拒绝同方差")
    set_cell_text(tbl, 5, 0, "Goldfeld-Quandt 检验")
    set_cell_text(tbl, 5, 1, "F=0.979, p=0.857 → 不拒绝同方差")
    set_cell_text(tbl, 6, 0, "Durbin-Watson 统计量")
    set_cell_text(tbl, 6, 1, "1.966 → 无自相关")
    set_cell_text(tbl, 7, 0, "Cook's D 异常点比例")
    set_cell_text(tbl, 7, 1, "4.74%（947/20,000）超过阈值")
    set_cell_text(tbl, 8, 0, "HC3 下显著性改变量")
    set_cell_text(tbl, 8, 1, "1个变量（fiveYearsProperty_1.0）")

    # 段 [94]: 多重共线性讨论
    p94_new = (
        "VIF 诊断显示，buildingStructure_6（VIF=492.4）和 buildingStructure_2（VIF=468.8）存在极端的多重共线性。"
        "这与 buildingStructure 变量的类别分布密切相关：某些结构类别（如钢结构）的占比极低，"
        "导致相应的虚拟变量与其他结构类别之间呈现近乎完全的线性关系。"
        "此外，square（22.4）和 log_square（20.9）之间的高度相关性也反映了面积变量在对数-线性变换后的共线性问题。"
        "部分年份虚拟变量（trade_year_2016、2015、2017）的 VIF 超过 10，"
        "这是在高基期（2011 年）上多年度同时纳入模型时的自然结果。"
    )
    replace_para_text(doc, 94, p94_new)

    p95_new = (
        "对于以 OLS 为基础的统计论文，9 个 VIF > 10 的变量虽然不影响模型的整体预测能力，"
        "但会膨胀个体系数的标准误、降低估计精度。"
        "值得注意的是，加入时间固定效应后条件数从 7.84×10⁶ 降至 4.59×10⁵（降幅约 94%），"
        "这是因为原模型中的 trade_year 连续变量与其平方项之间存在大量共线性，"
        "被年份虚拟变量替代后这一来源得到消除。"
        "在 OLS + 多项式模型中，多重共线性问题因高阶项的加入而急剧恶化，详见第 5.3 节。"
    )
    replace_para_text(doc, 95, p95_new)

    # 段 [97]: 异方差
    p97_new = (
        "Breusch-Pagan 检验在 1% 水平上显著拒绝同方差假设（p = 1.8×10⁻¹⁵⁹），"
        "而 Goldfeld-Quandt 检验未能检测到异方差（p = 0.857）。"
        "两个检验结论的不一致根源在于检验功效和敏感性的差异：BP 检验对一般形式的异方差均敏感，"
        "而 GQ 检验仅对排序后单调变化的方差敏感。"
        "残差诊断图中的「漏斗状」模式——拟合值增大时残差幅度的扩散——明确支持 BP 检验的结论，"
        "即样本中存在不可忽略的异方差。"
    )
    replace_para_text(doc, 97, p97_new)

    # 段 [101]: 稳健标准误
    p101_new = (
        "采用 HC3 稳健标准误对 OLS 系数进行校正。"
        "结果表明：HC3 校正后仅 1 个变量（fiveYearsProperty_1.0）的显著性判断发生改变"
        "（从 p=0.048 变为 p=0.053，略超 5% 阈值）。"
        "这一结果优于原模型（3 个变量显著性改变），"
        "说明加入时间固定效应后异方差对推断的干扰进一步减弱。"
        "因此，HC3 稳健标准误的使用主要作为学术严谨性的必要组成部分，"
        "而非因为实质性改变了结论。"
    )
    replace_para_text(doc, 101, p101_new)

    # ===== 10. 更新 六、模型比较 =====
    print("更新 六、模型比较...")

    # 更新模型比较表格（Table 2）
    tbl2 = doc.tables[2]
    set_cell_text(tbl2, 1, 1, "0.8294")
    set_cell_text(tbl2, 1, 2, "9411")
    set_cell_text(tbl2, 1, 3, "6471")
    set_cell_text(tbl2, 1, 4, "-207770")
    set_cell_text(tbl2, 2, 1, "0.8218")
    set_cell_text(tbl2, 2, 2, "9621")
    set_cell_text(tbl2, 2, 3, "6631")
    set_cell_text(tbl2, 2, 4, "-205038")
    set_cell_text(tbl2, 3, 1, "0.8185")
    set_cell_text(tbl2, 3, 2, "9696")
    set_cell_text(tbl2, 3, 3, "6703")
    set_cell_text(tbl2, 3, 4, "-203859")
    set_cell_text(tbl2, 4, 1, "0.8185")
    set_cell_text(tbl2, 4, 2, "9696")
    set_cell_text(tbl2, 4, 3, "6703")
    set_cell_text(tbl2, 4, 4, "—")
    set_cell_text(tbl2, 5, 1, "0.8184")
    set_cell_text(tbl2, 5, 2, "9695")
    set_cell_text(tbl2, 5, 3, "6703")
    set_cell_text(tbl2, 5, 4, "-203867")
    set_cell_text(tbl2, 6, 1, "0.8180")
    set_cell_text(tbl2, 6, 2, "9710")
    set_cell_text(tbl2, 6, 3, "6713")
    set_cell_text(tbl2, 6, 4, "—")

    # 段 [108]: 模型比较文本
    p108_new = (
        "OLS + 多项式模型在预测指标上表现最佳（R²=0.829，RMSE=9,411元/㎡），"
        "较基准 OLS（R²=0.818，RMSE=9,696元/㎡）提升约 1.1 个百分点，RMSE 降低约 285 元/㎡。"
        "5 折交叉验证结果与测试集一致（CV R²=0.8295±0.002），排除了过拟合的可能。"
        "与旧版本模型（trade_year 为连续变量）相比，当前基准 OLS 的 R² 从 0.786 提升至 0.818"
        "（+3.2 个百分点），RMSE 从 10,428 降至 9,696（降幅 7.0%），"
        "充分说明时间固定效应设定的有效性。"
        "然而，OLS 与多项式模型之间的 R² 差距也从原来的 1.9 个百分点缩窄至 1.1 个百分点——"
        "这是因为时间固定效应已经捕捉了部分原来多项式模型才能拟合的非线性时间趋势。"
    )
    replace_para_text(doc, 108, p108_new)

    # 段 [104]: 开头描述
    p104_new = (
        "本研究比较了 6 种回归模型在测试集上的表现："
        "（1）OLS（全变量，含时间固定效应）、"
        "（2）Ridge 回归（交叉验证选 λ）、"
        "（3）LASSO 回归（交叉验证选 λ）、"
        "（4）OLS（共识筛选变量）、"
        "（5）OLS + 交互项（5 个关键变量的两两交互）、"
        "（6）OLS + 多项式（5 个关键变量的二次项与交互项，共 79 个特征）。"
        "关键连续变量从 6 个变为 5 个（trade_year 因转为虚拟变量不再参与多项式扩展）。"
    )
    replace_para_text(doc, 104, p104_new)

    # ===== 11. 重写 6.4 时间趋势讨论 =====
    print("重写 6.4 时间趋势讨论...")
    p126_new = (
        "在共识变量 OLS 模型中，年份虚拟变量的系数呈现清晰的递增模式："
        "trade_year_2012（+0.15）、trade_year_2013（+0.48）、trade_year_2014（+0.49）、"
        "trade_year_2015（+0.54）、trade_year_2016（+0.83）、trade_year_2017（+1.15），"
        "基期为 2011 年。这一序列的特征是：2013 年较 2012 年有大幅跳跃（+0.33），"
        "而 2013-2015 年间增幅相对平缓（年增约 0.03-0.05），"
        "2015 年后再次加速（2016 年 +0.29，2017 年 +0.32）。"
        "该模式与 EDA 中观察到的「2011-2015 年初平缓上涨、2015 下半年后加速攀升」完全吻合。"
    )
    replace_para_text(doc, 126, p126_new)

    p127_new = (
        "在旧版模型中 trade_year 被作为连续线性变量（系数 0.180），"
        "等效于为所有年份施加了「年增幅约 19.7%」的单一系数，"
        "这必然低估 2015 年后的涨幅并高估 2011-2014 年的涨幅。"
        "时间固定效应解决了这一问题，同时消解了旧版模型中需要依赖 trade_year² 项来部分捕捉非线性趋势的妥协。"
        "月度虚拟变量的系数也从 2 月（+0.046）逐步递增至 12 月（+0.190），"
        "反映了一年内的季节性价格上升趋势。"
    )
    replace_para_text(doc, 127, p127_new)

    # ===== 12. 更新 6.3 系数膨胀 =====
    print("更新 6.3 系数膨胀...")
    p122_new = (
        "图 7 展示了 OLS + 多项式模型中系数绝对值最大的 15 个变量。"
        "部分区域虚拟变量的系数绝对值达到 200 至 800 的量级。由于响应变量为 log(price)，"
        "这意味着某区域的边际效应为 exp(200) 至 exp(800) 倍，在经济含义上完全荒谬。"
    )
    replace_para_text(doc, 122, p122_new)

    p123_new = (
        "这一现象的根源在于：多项式扩展将 5 个关键变量（dist_center、Lat、Lng、ladderRatio、DOM）"
        "扩展为 20 个二次项和交互项。这些高阶项与已有的区域虚拟变量（district_*）之间存在严重的多重共线性"
        "——区域本身就是地理空间的离散化表示，而经纬度的多项式组合是对同一空间的连续函数逼近。"
        "二者高度相关导致正规方程（X′X）近乎奇异，条件数急剧恶化。"
        "回归系数在理论上趋向无穷大，"
        "呈现出 ±200 至 ±800 的反常值。值得注意的是，虽然 trade_year 已转为虚拟变量不再参与多项式扩展，"
        "但 dist_center 与 Lat/Lng 之间的空间共线性仍然足以引发矩阵病态。"
    )
    replace_para_text(doc, 123, p123_new)

    # ===== 13. 更新结论 =====
    print("更新结论...")
    # 段 [133]: 时间因素
    p133_new = (
        "时间因素具有非线性影响。年份虚拟变量系数从 2012 年的 +0.15 逐步递增至 2017 年的 +1.15，"
        "验证了 2015 年前后房价结构性加速的特征。时间固定效应的设定优于连续的 trade_year 线性变量。"
    )
    replace_para_text(doc, 133, p133_new)

    # 段 [135]: 模型选择
    p135_new = (
        "模型选择取决于研究目标。OLS + 多项式模型取得最高预测精度（R²=0.829，RMSE=9,411元/㎡），"
        "但高阶项导致系数膨胀至无法解释的程度。当研究侧重于经济推断时，"
        "纳入时间和区域双向固定效应的线性主效应模型（R²=0.818，RMSE=9,696元/㎡）是更可靠的选择。"
    )
    replace_para_text(doc, 135, p135_new)

    # 段 [136]: LASSO
    p136_new = (
        "LASSO 在本应用场景中失效。由于 64 个特征中多数与房价存在真实关联，稀疏性假设不成立，"
        "LASSO 的最优 alpha 趋近于零，模型退化为 OLS。"
    )
    replace_para_text(doc, 136, p136_new)

    # 段 [137]: 诊断
    p137_new = (
        "模型诊断揭示了异方差性问题，HC3 稳健标准误的采用改变了 1 个变量的显著性判断。"
        "加入时间固定效应后，条件数从 7.84×10⁶ 降至 4.59×10⁵，但 buildingStructure 类别的 VIF 仍高达 490+。"
    )
    replace_para_text(doc, 137, p137_new)

    # 段 [141]: 宏观变量局限
    p141_new = (
        "模型未纳入宏观经济变量（利率、M2增速、限购政策虚拟变量等），"
        "年份虚拟变量的系数可能混杂了时间趋势与宏观冲击的双重效应。"
        "这是线性固定效应模型的内在局限——无法区分「时间」本身和「随时间变化的其他因素」。"
    )
    replace_para_text(doc, 141, p141_new)

    # 段 [143]: 条件数局限 → 更新
    p143_new = (
        "条件数 4.59×10⁵ 表明设计矩阵仍存在一定病态性。"
        "虽然较原模型（7.84×10⁶）已有大幅改善，但 buildingStructure 虚拟变量和多项式模型的高阶项仍可导致矩阵接近奇异。"
        "后续研究可考虑主成分回归（PCR）或对 buildingStructure 类别进行合并。"
    )
    replace_para_text(doc, 143, p143_new)

    # ===== 保存 =====
    out_path = "report/分析报告_大修版.docx"
    doc.save(out_path)
    print(f"\n已保存: {out_path}")


if __name__ == "__main__":
    main()
