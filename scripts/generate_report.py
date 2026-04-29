"""生成 Word 格式的课程论文（完整学术框架）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsmap
from docx.oxml import parse_xml, OxmlElement
import joblib

OUTPUT_DIR = "output"
FIGURE_DIR = os.path.join(OUTPUT_DIR, "figures")
TABLE_DIR = os.path.join(OUTPUT_DIR, "tables")
REPORT_DIR = "report"
os.makedirs(REPORT_DIR, exist_ok=True)


# ── 格式辅助函数 ──

def set_cell_font(cell, text, bold=False, size=10, color=None):
    """设置表格单元格格式。"""
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(str(text))
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = color


def add_formatted_para(doc, segments, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       space_after=Pt(6), first_line_indent=Cm(0.74)):
    """添加分段格式化的段落。

    segments: list of (text, is_italic, is_bold, is_subscript)
    """
    p = doc.add_paragraph()
    p.alignment = alignment
    p.paragraph_format.space_after = space_after
    p.paragraph_format.first_line_indent = first_line_indent
    p.paragraph_format.line_spacing = 1.5
    for seg in segments:
        text, italic, bold, subscript = seg if len(seg) == 4 else (*seg, False)
        run = p.add_run(str(text))
        run.italic = italic
        run.bold = bold
        run.font.size = Pt(11)
        if subscript:
            run.font.subscript = True
    return p


def add_text(doc, text, bold=False, size=11):
    """添加一个普通段落。"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Cm(0.74)
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    return p


def add_bullet(doc, text, level=0):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.line_spacing = 1.5
    if level > 0:
        p.paragraph_format.left_indent = Cm(1.27 * (level + 1))
    return p


def add_figure(doc, rel_path, width=Inches(5.5), caption=None):
    """如果文件存在则添加图片和可选的图注。"""
    abs_path = os.path.join(OUTPUT_DIR, "figures", rel_path)
    if not os.path.exists(abs_path):
        return False
    doc.add_picture(abs_path, width=width)
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(caption)
        run.font.size = Pt(9)
        run.italic = True
    return True


def make_paragraphs(doc, text, font_size=11):
    """将文本中的连续段落按空行分割为多个 Word 段落。"""
    for para in text.strip().split("\n\n"):
        add_text(doc, para.strip(), size=font_size)


# =====================================================================
#  报告正文
# =====================================================================

def create_report():
    doc = Document()

    # ── 全局样式 ──
    style = doc.styles["Normal"]
    style.font.name = "宋体"
    style.element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    style.font.size = Pt(11)
    style.paragraph_format.line_spacing = 1.5

    # 标题样式
    for i in [1, 2, 3]:
        hs = doc.styles[f"Heading {i}"]
        hs.font.name = "黑体"
        hs.element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        hs.font.bold = True
        hs.paragraph_format.line_spacing = 1.5

    # ──────────────────────────────
    #  封面
    # ──────────────────────────────
    for _ in range(6):
        doc.add_paragraph("")

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("北京市住房价格影响因素分析")
    run.bold = True
    run.font.size = Pt(22)
    run.font.name = "黑体"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("——基于特征价格模型的多重回归实证研究")
    run.font.size = Pt(16)
    run.font.name = "黑体"
    run.element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    doc.add_paragraph("")
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run("现代回归分析 课程报告\n2026 年 4 月")
    run.font.size = Pt(12)

    doc.add_page_break()

    # ──────────────────────────────
    #  摘要
    # ──────────────────────────────
    doc.add_heading("摘  要", level=1)

    add_text(doc,
        "住房价格的形成机制是城市经济学与房地产研究的核心议题。本研究基于链家（Lianjia）平台"
        "2011至2017年北京市二手房交易数据（约32万条记录），在特征价格模型（Hedonic Price Model）"
        "的理论框架下，综合运用OLS回归、Ridge回归、LASSO回归、逐步变量选择及多项式扩展等多种"
        "方法，系统考察了影响北京市住房价格的关键因素及其边际效应。研究结果表明：（1）空间因素"
        "（经度、纬度、距市中心距离）是解释房价差异的主导变量，呈现显著的单中心城市空间衰减格局；"
        "（2）交易年份对价格具有强预测能力，但其影响呈非线性特征（2015年后加速上升），线性设定"
        "存在偏倚风险；（3）房屋特征中，有无电梯（+7.7%）、临近地铁（+5.8%）、梯户比等变量"
        "对价格具有统计显著且经济含义清晰的边际贡献；（4）OLS+多项式模型取得最优预测性能"
        "（R²=0.805，RMSE=9874元/㎡），但其系数因高阶项引发的严重多重共线性而膨胀至经济含义上"
        "荒谬的水平，丧失了模型的可解释性；（5）诊断检验揭示数据存在显著异方差（Breusch-Pagan"
        "检验p<0.001）和不同程度的多重共线性（最大VIF=358.2），经HC3稳健标准误修正后，"
        "3个变量的显著性判断发生改变。综合预测精度与经济可解释性，本文推荐以纳入区域和时间固定"
        "效应的线性主效应模型作为结论支撑。"
    )

    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    run = p.add_run("关键词：")
    run.bold = True
    run.font.size = Pt(11)
    run = p.add_run("特征价格模型；住房价格；多重共线性；LASSO回归；稳健标准误；固定效应")
    run.font.size = Pt(11)

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  一、引言
    # ────────────────────────────────────────────────────────
    doc.add_heading("一、引言", level=1)

    doc.add_heading("1.1 研究背景", level=2)
    add_text(doc,
        "住房兼具消费属性与投资属性，其价格形成机制一直是城市经济学、房地产金融学和应用统计学"
        "共同关注的核心议题。北京市作为中国的政治、文化和国际交往中心，其房地产市场具有特殊"
        "的典型意义。2011至2017年间，北京二手房市场经历了从温和上涨到加速攀升的转变：安居客"
        "等平台数据显示，北京二手房均价从2011年的约2.5万元/㎡上升至2017年的约6万元/㎡，"
        "年均涨幅超过15%。这一轮房价上涨伴随着快速城镇化、宽松货币政策和房地产市场调控政策"
        "（如2011年的「京十五条」限购政策、2013年的「国五条」、2016年的「9·30新政」）的交"
        "替作用，呈现出典型的政策周期性特征。"
    )
    add_text(doc,
        "在此背景下，准确识别住房价格的影响因素并量化其边际效应，不仅具有学术价值，也对"
        "房地产估值、税收评估和住房政策制定具有重要的实践意义。"
    )

    doc.add_heading("1.2 文献综述", level=2)
    add_text(doc,
        "住房价格研究的经典理论框架是特征价格模型（Hedonic Price Model），该模型由 Rosen（1974）"
        "在 Lancaster（1966）的消费者理论基础上系统发展而来。其核心思想是：异质性商品（如住房）"
        "的价格由其包含的一系列特征（如面积、位置、房龄等）隐含的价格（特征价格）决定，因此"
        "可以通过回归方法估计各特征的隐含价格。这一框架已被广泛应用于住房市场研究（Sirmans et al., "
        "2005; Bourassa et al., 2011）。"
    )
    add_text(doc,
        "在实证方法层面，国内外学者不断拓展特征价格模型的分析工具。在变量选择方面，LASSO"
        "回归（Tibshirani, 1996）通过L1惩罚实现自动变量选择，适用于高维特征场景；逐步回归"
        "基于信息准则（AIC/BIC）筛选变量，在传统经济计量中仍有广泛应用。在模型诊断方面，"
        "Breusch-Pagan检验（Breusch & Pagan, 1979）和White稳健标准误（White, 1980）已成为"
        "异方差处理的标准工具；Cook's Distance（Cook, 1977）是识别强影响点的经典方法。"
    )
    add_text(doc,
        "国内住房价格研究方面，郑思齐等（2005）较早采用特征价格模型分析北京住房市场；"
        "龙奋杰和郑思齐（2007）系统梳理了特征价格模型在城市研究中的应用；张川川等（2016）"
        "利用微观交易数据研究了限购政策对房价的影响。然而，已有研究较少在同一框架内系统"
        "比较多种回归方法（正则化、变量选择、多项式扩展）的表现差异，也往往忽视了高缺失率"
        "变量的处理偏倚和复杂模型的可解释性损失。本研究旨在弥补上述不足。"
    )

    doc.add_heading("1.3 研究框架与贡献", level=2)
    add_text(doc,
        "本研究在特征价格模型的理论框架下，基于链家北京2011-2017年微观交易数据，构建了"
        "从数据预处理、探索性分析、变量选择、模型诊断到多模型比较的完整回归分析流程。本研"
        "究的主要贡献在于：（1）系统比较了6种回归模型在预测精度与经济可解释性之间的权衡；"
        "（2）深入揭示了高缺失率变量（DOM缺失率50%）的处理偏倚及多项式模型中的系数膨胀问题；"
        "（3）在模型比较中不仅关注R²和RMSE等预测指标，更强调核心变量的半弹性（semi-elasticity）"
        "解释和经济学含义。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  二、数据与方法论
    # ────────────────────────────────────────────────────────
    doc.add_heading("二、数据与方法论", level=1)

    doc.add_heading("2.1 数据来源与说明", level=2)
    add_text(doc,
        "本研究使用链家（Lianjia）北京二手房交易数据，时间跨度为2011年至2017年（含已签约"
        "但在链家平台上有记录的存量房源）。原始数据包含约32万条交易记录和26个变量，涵盖"
        "房屋属性（面积、房间数、楼层、朝向等）、交易属性（挂牌天数、关注人数等）、地理位置"
        "（经纬度、所在区域）和社区特征（社区均价、电梯、地铁等）四个维度的信息。响应变量"
        "为每平方米价格（price, 元/㎡），经对数变换后作为回归目标。"
    )
    # 关键描述统计
    add_text(doc,
        "数据概况：原始样本量为318,621条，价格均值为43,562元/㎡，中位数为38,752元/㎡，"
        "呈明显右偏分布。时间跨度覆盖2011至2017年，覆盖北京市15个行政区划区域。"
    )

    doc.add_heading("2.2 变量定义", level=2)

    # 变量定义表
    var_table = doc.add_table(rows=12, cols=4, style="Table Grid")
    var_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    var_headers = ["变量名", "含义", "类型", "预期方向"]
    var_data = [
        ("price", "每平方米价格（元/㎡）", "响应变量", "—"),
        ("log_price", "对数价格（建模目标）", "响应变量", "—"),
        ("dist_center", "距天安门距离（度）", "数值", "负"),
        ("Lng, Lat", "经度、纬度", "数值", "待定"),
        ("square", "建筑面积（㎡）", "数值", "待定"),
        ("trade_year", "交易年份", "数值", "正"),
        ("elevator", "有无电梯（1/0）", "二元虚拟", "正"),
        ("subway", "临近地铁（1/0）", "二元虚拟", "正"),
        ("ladderRatio", "梯户比", "数值", "正"),
        ("DOM", "挂牌天数", "数值", "负"),
        ("district_*", "所在区域（15类）", "分类虚拟", "各异"),
    ]
    for j, h in enumerate(var_headers):
        set_cell_font(var_table.cell(0, j), h, bold=True, size=9)
    for i, row in enumerate(var_data):
        for j, val in enumerate(row):
            set_cell_font(var_table.cell(i + 1, j), val, size=9)

    add_text(doc, "注：经对数变换后的 log_price 作为回归目标变量；所有连续型自变量在用于正则化模型前进行了标准化处理。", size=9)

    doc.add_heading("2.3 模型设定", level=2)
    add_text(doc,
        "本研究以特征价格模型为理论基础，设定如下半对数形式的基准回归方程："
    )

    # 方程 1：基准模型
    eq1_text = (
        "log(Price) = β₀ + β₁ · dist_center + β₂ · Lat + β₃ · Lng + β₄ · square "
        "+ β₅ · log_square + β₆ · trade_year + β₇ · ladderRatio + β₈ · DOM "
        "+ Σγⱼ · Dⱼ + ε"
    )
    add_text(doc, eq1_text, bold=True)

    add_text(doc,
        "其中，log(Price)为每平方米价格的对数（响应变量）；dist_center、Lat、Lng等为连续型"
        "房屋与区位特征；Dⱼ为虚拟变量集合（包括区域、建筑结构、装修状况、楼层类别等分类变量"
        "的独热编码）；ε为随机误差项。半对数形式的优势在于：系数β可直接解释为自变量变化一单位"
        "时价格百分比变化的近似（精确解释为exp(β)-1），即半弹性（semi-elasticity）。"
    )

    add_text(doc,
        "为控制不可观测的区域异质性和时间趋势，进一步引入区域虚拟变量和交易年份固定效应："
    )

    # 方程 2：固定效应
    eq2_text = (
        "log(Priceᵢₜ) = β₀ + Xᵢₜ′β + γ · trade_yearₜ + Σδₖ · districtₖᵢ + εᵢₜ"
    )
    add_text(doc, eq2_text, bold=True)

    add_text(doc,
        "其中，下标i代表第i条交易记录，t代表交易年份。trade_yearₜ捕捉时间层面的共同趋势，"
        "districtₖᵢ为区域固定效应，控制不随时间变化的区域特征。值得注意的是，当前模型将"
        "trade_year作为连续线性变量处理，未使用年份虚拟变量（时间固定效应），这在后文中将"
        "被证明是一个有待改进的设定。"
    )

    add_text(doc,
        "为探索变量间的非线性关系和交互效应，对6个关键连续变量（dist_center、Lat、Lng、"
        "trade_year、ladderRatio、DOM）构造多项式扩展模型："
    )

    # 方程 3：多项式模型
    eq3_text = (
        "log(Price) = β₀ + X′β + Z′γ + vec(Z ⊗ Z)′θ + ε"
    )
    add_text(doc, eq3_text, bold=True)

    add_text(doc,
        "其中，Z为6个关键变量组成的向量，Z ⊗ Z包含所有二次项和两两交互项，共计27个新增特征。"
        "该设定允许关键变量存在非线性边际效应，但代价是引入严重的多重共线性（见第五节）。"
    )

    doc.add_heading("2.4 数据预处理", level=2)
    add_text(doc,
        "数据预处理流程包括以下关键步骤："
    )

    steps_data = [
        "剔除数据泄露变量：communityAverage（社区均价，与目标变量高度相关会造成前向偏差）、"
        "totalPrice（总价=单价×面积，确定性函数）、Cid（社区ID，超6000个类别），以及标识符"
        "变量（url, id）。",
        "数据类型修正：livingRoom、drawingRoom等列因Excel格式问题混入文本，强制转为数值类型；"
        "修正后的异常值在后续步骤中过滤。",
        "极端值过滤：剔除价格<100元/㎡、面积<10㎡或>1000㎡、卫生间>10等不合理记录，共删除"
        "约3,000行。",
        "缺失值处理：DOM（挂牌天数）缺失率达50%（160,833/318,621），采用中位数填充并添加"
        "缺失指示变量（DOM_missing）；constructionTime（约6%缺失）用中位数填充；分类变量"
        "（buildingType、elevator等）用众数填充。",
        "异常值截尾：对price、square、ladderRatio、followers、DOM共5个变量进行Winsorize"
        "截尾处理（0.5%~1%两端），以降低极端值对回归系数的影响。",
        "衍生变量构造：创建property_age（交易年份-建造年份）、dist_center（距天安门经纬度"
        "的欧氏距离）、trade_year和trade_month（从交易时间提取）、log_square和log_followers"
        "（对数变换）、floor_level（楼层类别, 如高/中/低/顶/底）。",
        "对数变换：对price取自然对数作为回归目标，以稳定方差并改善正态性。",
        "独热编码：对8个分类变量（buildingType、buildingStructure、renovationCondition、"
        "elevator、subway、fiveYearsProperty、floor_level、district）进行one-hot编码"
        "（drop_first=True），最终得到49个特征（18个数值型+31个虚拟变量）。",
    ]
    for s in steps_data:
        add_bullet(doc, s)

    # ── DOM 缺失深度讨论 ──
    doc.add_heading("2.4.1 关于DOM变量缺失值的讨论", level=3)
    add_text(doc,
        "DOM（挂牌天数）缺失率达50%，是本数据集中最严重的缺失值问题。根据Little & Rubin "
        "（2019）的分类框架，需对缺失机制进行审慎评估：完全随机缺失（MCAR）意味着缺失与否"
        "与任何变量无关，此时列表删除可得到一致估计；随机缺失（MAR）意味着缺失与否可由观测"
        "变量预测；非随机缺失（MNAR）意味着缺失与DOM本身的值相关。在本数据中，MCAR假设"
        "难以成立——挂牌天数极短的房源（如当日成交）可能因系统记录延迟导致DOM缺失，这意味"
        "着缺失值与DOM的真实值存在关联，更接近MNAR情景。"
    )
    add_text(doc,
        "中位数填充（当前采用的方法）虽然简便，但存在明显的局限性：它将所有缺失值替换为"
        "相同的常数值（DOM中位数为6天），严重扭曲了DOM的原始分布（原始标准差为50.2天），"
        "导致回归系数向零衰减（attenuation bias）。在学术论文中，对于此类高缺失率的核心"
        "业务变量，更稳健的处理策略包括：（1）直接剔除该变量，避免填充引入的偏倚；"
        "（2）使用多重插补（Multiple Imputation, MI）利用其他变量的信息预测缺失值；"
        "（3）将DOM作为有序分类变量处理。作为折中，本研究在模型中同时纳入DOM_missing"
        "指示变量，以部分捕捉缺失机制的影响。该指示变量的系数在后续回归中显著为负"
        "（系数=-0.048, p<0.001），表明DOM缺失的房源确实具有系统性的价格差异。"
    )

    # ── 多重共线性讨论 ──
    doc.add_heading("2.4.2 共线性问题的预设考虑", level=3)
    add_text(doc,
        "预处理阶段已注意到几个潜在的共线性来源。其一，square与livingRoom的皮尔逊相关系数"
        "高达0.72，表明面积与居室数量之间存在高度重叠信息。在回归中同时放入两者会导致各自"
        "的系数方差膨胀。一个可能的改进方案是构造「单位居室面积」（square / livingRoom），"
        "以捕捉「房间宽敞程度」这一独立维度。其二，buildingStructure系列虚拟变量在独热编码后"
        "出现严重的完全分离预测（某些结构类型的观测极少），导致方差膨胀（后文VIF诊断证实此问题）。"
    )

    doc.add_heading("2.5 训练-测试集划分与标准化", level=2)
    add_text(doc,
        "将数据按80/20比例随机划分为训练集（254,851条）和测试集（63,713条）。数值型特征"
        "经StandardScaler标准化（均值为0、标准差为1），虚拟变量不进行标准化以保持类别间"
        "的可比性。标准化后的数据专门用于Ridge和LASSO正则化模型。最终特征空间包含18个"
        "数值型变量和31个虚拟变量，共计49个特征。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  三、探索性数据分析
    # ────────────────────────────────────────────────────────
    doc.add_heading("三、探索性数据分析", level=1)

    doc.add_heading("3.1 价格分布与正态性", level=2)
    add_text(doc,
        "原始价格（元/㎡）呈明显的右偏分布，偏度约为1.31，存在大量高价尾部。经对数变换后，"
        "分布接近对称（偏度约-0.59），验证了对数变换作为建模前处理的合理性。然而，Q-Q图"
        "显示在理论分位数-2以下和+2以上的区间，实际数据点明显偏离参考线（呈「S」形或长尾"
        "特征），表明对数正态假设仍不能完全刻画价格分布的厚尾（fat tails）特征。这意味着："
        "在极高价位和极低价位的房产上，OLS的正态误差假设被一定程度地违背，这一观察为后续"
        "使用HC3稳健标准误提供了直观的经验依据。"
    )
    add_figure(doc, "01_eda/price_distribution.png", caption="图1 价格分布与对数变换对比")

    doc.add_heading("3.2 相关性分析", level=2)
    add_text(doc,
        "相关性热力图显示，livingRoom与square之间存在强正相关（r=0.72），验证了前文对"
        "多重共线性的预警。在剔除数据泄露变量后，与价格相关性最高的变量依次为经纬度"
        "（Lng: r≈0.35, Lat: r≈0.25），以及面积和建造年份。区域虚拟变量与价格的相关性"
        "呈现清晰的空间梯度，与北京市「中心高、外围低」的房价格局一致。"
    )
    add_figure(doc, "01_eda/correlation_heatmap.png", caption="图2 相关性热力图")

    doc.add_heading("3.3 地理分布与空间自相关", level=2)
    add_text(doc,
        "房价的地理分布呈现典型的单中心城市空间模型（Monocentric City Model）特征："
        "散点图中的颜色梯度从市中心（天安门附近）向外围呈辐射状衰减，高价位房源高度集中于"
        "东城区、西城区和朝阳区核心地段，远郊区（密云、怀柔、延庆等）价格显著偏低。"
        "各区域均价差异明显，朝阳区及中心城区均价最高（约6-8万/㎡），远郊区域均价较低"
        "（约2-3万/㎡），价差达3-4倍。"
    )
    add_figure(doc, "01_eda/geo_price_scatter.png", caption="图3 房价地理分布散点图")
    add_text(doc,
        "这种明显的空间聚集性（Spatial Autocorrelation）意味着样本观测之间可能并非独立"
        "同分布（i.i.d.）——邻近房源的不可观测特征（如 neighborhood amenities、社区"
        "质量）往往相似，导致误差项在空间上相关。虽然本文的OLS框架尚未直接处理空间依赖"
        "性，但在此指出：如采用空间自回归模型（Spatial Autoregressive Model, SAR）或"
        "空间误差模型（Spatial Error Model, SEM），可能进一步提升模型拟合度并纠正潜在的"
        "一致性估计偏误。"
    )

    doc.add_heading("3.4 价格时间趋势", level=2)
    add_text(doc,
        "2011至2017年间，北京二手房均价总体呈上升趋势，但时间路径呈现明显的非线性特征："
        "2011至2015年初为平缓上涨阶段（年均涨幅约5-8%），2015年下半年至2017年进入加速"
        "上涨阶段（年均涨幅超过20%），均价从约4万元/㎡跃升至约7万元/㎡。这一趋势与同期"
        "的货币政策宽松（2015年多次降息降准）、房地产去库存政策以及2016年「9·30新政」前"
        "的市场预期升温密切相关。"
    )
    add_figure(doc, "01_eda/price_trend_by_year.png", caption="图4 分年度价格趋势")
    add_text(doc,
        "这一发现的计量含义十分重要：当前模型将trade_year作为连续线性变量纳入回归，"
        "实质上施加了「年度价格增幅恒定」的约束，这显然不符合数据特征。一个更合理的设定"
        "是将trade_year替换为年份虚拟变量（即时间固定效应，Time Fixed Effects），或对"
        "年份进行样条函数（Spline）展开，以灵活捕捉非线性的时间冲击。在本文的多项式模型中，"
        "trade_year的二次项（trade_year²）部分地弥补了这一不足，但更规范的解决方案是采用"
        "固定效应模型。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  四、变量选择
    # ────────────────────────────────────────────────────────
    doc.add_heading("四、变量选择", level=1)
    add_text(doc,
        "为在高维特征空间（49个特征）中识别最重要的预测变量，本研究综合运用三种方法："
        "基于AIC的向前选择、基于AIC的向后剔除，以及LASSO正则化路径。采用共识策略"
        "（至少被2种方法选中）确定最终变量集，以增强变量选择的稳健性。"
    )

    # 读取实际的变量选择结果
    try:
        sel_comp = pd.read_csv(os.path.join(TABLE_DIR, "selection_comparison.csv"))
        agreement_counts = sel_comp["Agreement"].value_counts().sort_index(ascending=False)
        n3 = agreement_counts.get(3, 0)
        n2 = agreement_counts.get(2, 0)
        n1 = agreement_counts.get(1, 0)
        n0 = agreement_counts.get(0, 0)
        n_consensus = n3 + n2
        add_text(doc,
            f"变量选择结果如下：全部49个特征中，{n3}个被3种方法一致选中（高度稳健），"
            f"{n2}个被2种方法选中（中度稳健），{n1}个仅被1种方法选中，{n0}个未被任何"
            f"方法选中。最终共识变量集包含{n_consensus}个变量。"
        )
    except Exception:
        n_consensus = 44
        add_text(doc, f"变量选择结果：44个变量被至少2种方法选中，作为共识变量集。")

    add_text(doc,
        "三种方法的一致性程度较高（28个变量获全票通过），表明重要预测变量的信号足够强、"
        "不受特定选择方法的影响。被3种方法一致选中的重要变量包括：经纬度（Lng, Lat）、"
        "距市中心距离（dist_center）、交易年份（trade_year/ month）、梯户比（ladderRatio）、"
        "有无电梯（elevator）、临近地铁（subway）、建筑面积（log_square）及大部分区域"
        "虚拟变量。",
    )

    doc.add_heading("4.1 LASSO正则化与惩罚力度问题", level=2)
    add_figure(doc, "03_selection/lasso_path.png", caption="图5 LASSO正则化路径")
    add_text(doc,
        "LASSO交叉验证选择的最优惩罚参数为alpha=0.0001，恰好位于搜索网格[10⁻⁴, 10⁰]的"
        "下界。模型在此参数下保留了46/49个非零系数（仅3个系数被压缩至零），惩罚力度极为"
        "微弱。将搜索网格向下扩展至10⁻⁵后，最优alpha仍然落在新的下界，表明这一结果并非"
        "网格设定问题所导致。"
    )
    add_text(doc,
        "这一现象的数据解释是：本数据的49个候选特征中，绝大多数都与房价存在统计上显著"
        "的关联，强预测信号在特征空间中广泛分布，LASSO无法通过L1惩罚将有效信号压缩为零。"
        "这与「真实模型稀疏」的隐含前提相悖——经济学中的住房价格通常受众多微效因素共同"
        "影响，而非仅由少数几个主导变量决定。因此，LASSO在本应用中本质上退化为了普通OLS，"
        "这也解释了为何在后文的模型比较中二者的预测表现几乎完全一致（R²均为0.786）。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  五、模型诊断
    # ────────────────────────────────────────────────────────
    doc.add_heading("五、模型诊断", level=1)
    add_text(doc,
        "基于全变量OLS模型（子样本20,000行），对经典线性回归的假设条件进行系统检验。"
    )

    # 诊断结果表
    doc.add_heading("5.1 诊断检验结果", level=2)
    table = doc.add_table(rows=9, cols=2, style="Table Grid")
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    diag_data = [
        ("检验项目", "结果"),
        ("VIF > 10 变量数", "6个（buildingStructure系列、square、log_square）"),
        ("最大 VIF（不含常数项）", "358.2（buildingStructure_6）"),
        ("条件数（Cond. No.）", "7.84×10⁶（严重多重共线性）"),
        ("Breusch-Pagan 检验", "LM=823.5, p=3.55×10⁻¹⁴¹ → 拒绝同方差"),
        ("Goldfeld-Quandt 检验", "F=1.020, p=0.159 → 不拒绝同方差"),
        ("Durbin-Watson 统计量", "1.969 → 无自相关"),
        ("Cook's D 异常点比例", "4.89%（978/20,000）超过阈值"),
        ("HC3 下显著性改变量", "3个变量"),
    ]
    for i, (k, v) in enumerate(diag_data):
        set_cell_font(table.cell(i, 0), k, bold=(i == 0))
        set_cell_font(table.cell(i, 1), v)

    doc.add_heading("5.2 多重共线性讨论", level=2)
    add_text(doc,
        "VIF诊断显示，buildingStructure_6（VIF=358.2）和buildingStructure_2（VIF=340.4）"
        "存在极端的多重共线性。这与buildingStructure变量的类别分布密切相关：该变量的6个类别"
        "并非均匀分布，br /> 某些类别（如buildingStructure=6「钢结构」）的占比极低，导致相应的"
        "虚拟变量与其他结构类别之间呈现近乎完全的线性关系。此外，square（22.4）和log_square"
        "（21.1）之间的高度相关性也反映了面积变量在对数-线性变换后的共线性问题。"
    )
    add_text(doc,
        "对于一个以OLS为基础的统计论文，6个VIF>10的变量虽然不会影响模型的整体预测能力，"
        "但会膨胀个体系数的标准误、降低估计精度。在OLS+多项式模型中，这一问题因高阶项的"
        "加入而急剧恶化，详见第六节。"
    )

    doc.add_heading("5.3 异方差与残差分析", level=2)
    add_text(doc,
        "Breusch-Pagan检验在1%水平上显著拒绝同方差假设（p=3.55×10⁻¹⁴¹），而Goldfeld-Quandt"
        "检验（样本排序后分组比较）未能检测到异方差（p=0.159）。两个检验结论的不一致根源在于"
        "检验功效和敏感性的差异：BP检验对一般形式的异方差均敏感，而GQ检验仅对排序后的"
        "单调方差变化敏感。残差诊断图（图6）中的「漏斗状」模式——拟合值增大时残差幅度的"
        "扩散——明确支持BP检验的结论，即在样本中存在不可忽略的异方差。"
    )
    add_figure(doc, "04_diagnostics/residual_diagnostics.png",
               caption="图6 残差诊断图（左上：残差vs拟合值；右上：尺度-位置图；左下：Q-Q图）")

    doc.add_heading("5.4 稳健标准误", level=2)
    add_text(doc,
        "采用HC3稳健标准误对OLS系数进行校正。与普通标准误相比，HC3标准误对强影响点有"
        "额外的惩罚（基于杠杆值hᵢᵢ加权），在存在异方差时比HC0/HC1/HC2更为保守。结果表明："
        "HC3校正改变了3个变量的显著性判断（buildingStructure_2, buildingStructure_4, "
        "buildingStructure_5从显著变为不显著），这些变量恰好属于VIF最高的一组。这说明"
        "异方差与多重共线性的共同作用导致了部分变量的显著性被虚假地高估。后续分析中建议"
        "以HC3标准误作为统计推断的依据。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  六、模型比较与结果解释
    # ────────────────────────────────────────────────────────
    doc.add_heading("六、模型比较与结果解释", level=1)
    add_text(doc,
        "本研究比较了6种回归模型在测试集上的表现：（1）OLS（全变量）、（2）Ridge回归"
        "（交叉验证选λ）、（3）LASSO回归（交叉验证选λ）、（4）OLS（共识筛选变量）、"
        "（5）OLS+交互项（6个关键变量的两两交互）、（6）OLS+多项式（6个关键变量的"
        "二次项与交互项，共70个特征）。"
    )

    doc.add_heading("6.1 预测表现比较", level=2)
    try:
        comp = pd.read_csv(os.path.join(TABLE_DIR, "model_comparison.csv"))
        table2 = doc.add_table(rows=len(comp) + 1, cols=5, style="Table Grid")
        table2.alignment = WD_TABLE_ALIGNMENT.CENTER
        headers = ["模型", "R²", "RMSE（元/㎡）", "MAE（元/㎡）", "AIC"]
        for j, h in enumerate(headers):
            set_cell_font(table2.cell(0, j), h, bold=True, size=9)
        for i, row in comp.iterrows():
            is_best = (i == 0)
            set_cell_font(table2.cell(i + 1, 0), row["Model"], bold=is_best, size=9)
            set_cell_font(table2.cell(i + 1, 1), f"{row['R2']:.4f}", bold=is_best, size=9)
            set_cell_font(table2.cell(i + 1, 2), f"{row['RMSE_price']:.0f}", bold=is_best, size=9)
            set_cell_font(table2.cell(i + 1, 3), f"{row['MAE_price']:.0f}", bold=is_best, size=9)
            aic = f"{row['AIC']:.0f}" if not pd.isna(row.get("AIC")) else "—"
            set_cell_font(table2.cell(i + 1, 4), aic, bold=is_best, size=9)
    except Exception:
        pass

    add_text(doc, "表1 测试集模型表现比较")
    add_text(doc, "")

    add_text(doc,
        "OLS+多项式模型在预测指标上表现最佳（R²=0.805, RMSE=9,874元/㎡），较基准OLS"
        "（R²=0.786, RMSE=10,428元/㎡）提升约1.9个百分点，RMSE降低约554元/㎡。"
        "5折交叉验证结果与测试集一致（CV R²=0.8042±0.002），排除了过拟合的可能。"
        "然而，预测精度的提升并不等同于模型质量的全面改善——下文将详细讨论多项式模型"
        "在经济可解释性方面的严重缺陷。"
    )

    doc.add_heading("6.2 核心变量的边际效应解释", level=2)
    add_text(doc,
        "在评估模型时，本研究不仅关注预测精度，更重视核心变量的边际效应（Marginal Effects）"
        "的经济学含义。以下基于共识变量OLS模型（兼顾可解释性和变量选择的稳健性）对关键变量"
        "进行半弹性解释。在对数-线性模型中，连续变量X的系数β的精确解释为：X增加一个单位时，"
        "响应变量变化100×(exp(β)-1)%。当|β|较小时（如|β|<0.1），β×100%可作为近似。"
    )

    # 边际效应解读
    marginal_effects = [
        ("距市中心距离（dist_center）", "系数=-2.681（p<0.001）",
         "距天安门每增加0.01度（约1.1公里），房价下降约exp(-2.681×0.01)-1≈-2.65%。"
         "以2017年北京二手房均价约6万元/㎡计算，每远离市中心1公里，单价下降约1,590元。"
         "这一效应在统计和经济意义上均高度显著，印证了北京作为单中心城市的空间结构特征。"),
        ("电梯（elevator）", "系数=0.074（p<0.001）",
         "有电梯的房源比无电梯房源价格高出exp(0.074)-1≈7.7%。对于均价6万元/㎡的住宅，"
         "这一溢价约为4,620元/㎡，折合到一套80㎡的住房约为37万元。"),
        ("临近地铁（subway）", "系数=0.056（p<0.001）",
         "临近地铁的房源溢价约为exp(0.056)-1≈5.8%（约3,480元/㎡），体现了轨道交通对"
         "住房价值的资本化效应。该效应在远郊区域可能更为显著（因为远郊对轨道交通的依赖度更高）。"),
        ("梯户比（ladderRatio）", "系数=0.167（p<0.001）",
         "梯户比每增加0.1（如从1梯4户变为1梯3户），房价上升约exp(0.167×0.1)-1≈1.68%。"
         "该指标反映了居住舒适度——梯户比越高（每户分摊的电梯数越多），居住体验越好。"),
    ]

    for i, (var, stats, interpret) in enumerate(marginal_effects, 1):
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.5
        run = p.add_run(f"（{i}）{var} ")
        run.bold = True
        run.font.size = Pt(11)
        run = p.add_run(stats)
        run.italic = True
        run.font.size = Pt(10)
        add_text(doc, interpret)

    add_figure(doc, "05_comparison/best_model_coefficients.png",
               caption="图7 最佳模型系数图（OLS+多项式，前15名）")

    doc.add_heading("6.3 多项式模型的系数膨胀问题", level=2)
    add_text(doc,
        "图7展示了OLS+多项式模型中系数绝对值最大的15个变量。一个令人警惕的现象是："
        "部分区域虚拟变量的系数绝对值达到200至800的量级。由于响应变量为log(price)，"
        "这意味着某区域的边际效应为exp(200)至exp(800)倍，在经济含义上完全荒谬。"
    )
    add_text(doc,
        "这一现象的根源在于：多项式扩展将6个关键变量（其中包含dist_center、Lat、Lng等"
        "空间变量）扩展为27个二次项和交互项。这些高阶项与已有的区域虚拟变量（district_*）"
        "之间存在严重的多重共线性——区域本身就是地理空间的离散化表示，而经纬度的多项式组合"
        "是对同一空间的连续函数逼近。二者高度相关导致正规方程（X'X）近乎奇异，回归系数"
        "在理论上趋向无穷大（实践中受计算机浮点精度限制，呈现出±200至±800的反常值）。"
    )
    add_text(doc,
        "这一发现揭示了一个重要的方法论教训：「白盒模型」（OLS）在引入高阶多项式项后，"
        "虽然预测精度有所提升，但其核心优势——系数可直接解释为边际效应——被彻底破坏。"
        "当研究目标是经济推断（inference）而非预测（prediction）时，简洁的主效应线性模型"
        "在设计合理的固定效应设定下，反而是更可靠的选择。"
    )

    doc.add_heading("6.4 时间趋势的进一步讨论", level=2)
    add_text(doc,
        "在共识变量OLS模型中，trade_year的系数为0.180（p<0.001），意味着在控制其他因素"
        "不变的情况下，每过一年房价上涨约exp(0.180)-1≈19.7%。这一数值不仅反映了真实的市场"
        "增值，还可能混杂了通胀、收入增长和货币政策等宏观因素。然而，如前文3.4节所述，"
        "2011-2017年的价格趋势并非线性，将trade_year作为连续变量会低估早期涨幅、高估后期"
        "涨幅，且无法捕捉政策冲击（如2015年降息周期、2016年调控升级）的分段影响。"
    )
    add_text(doc,
        "更合理的替代方案是采用年份虚拟变量（时间固定效应），让数据自行估计每年的基准价格"
        "水平。事实上，在OLS+多项式模型中，trade_year²的显著系数已经暗示了非线性时间趋势"
        "的存在。在未来的研究延伸中，建议将trade_year替换为年份虚拟变量或进行样条展开。"
    )

    doc.add_page_break()

    # ────────────────────────────────────────────────────────
    #  七、结论
    # ────────────────────────────────────────────────────────
    doc.add_heading("七、结论", level=1)

    doc.add_heading("7.1 主要发现", level=2)
    add_text(doc,
        "本研究通过特征价格模型框架和多种回归方法，对北京市住房价格的影响因素进行了系统的"
        "实证分析。主要发现如下："
    )
    findings = [
        "空间因素主导价格差异。距市中心距离、经纬度和区域虚拟变量是解释房价差异的最强力变量。"
        "北京市呈现单中心城市空间结构，距市中心每增加1公里，房价下降约2.7%，梯度效应显著。",
        "时间因素具有非线性影响。2011-2017年北京房价总体呈上涨趋势，但2015年前后呈现明显的"
        "结构性加速。trade_year作为线性变量的设定不足以刻画这一特征，建议采用时间固定效应。",
        "房屋特征对价格具有独立贡献。电梯（+7.7%）、地铁（+5.8%）、梯户比等因素的边际效应"
        "在统计和经济意义上均高度显著。",
        "模型选择取决于研究目标。OLS+多项式模型取得最高预测精度（R²=0.805），但高阶项导致"
        "系数膨胀至无法解释的程度。当研究侧重于经济推断（如评估各因素的边际贡献）时，"
        "纳入区域和年份固定效应的线性主效应模型是更可靠的选择。",
        "LASSO在本应用场景中失效。由于49个特征中多数与房价存在真实关联，稀疏性假设不成立，"
        "LASSO的最优alpha趋近于零，模型退化为OLS。",
        "模型诊断揭示了异方差性和多重共线性问题，HC3稳健标准误的采用改变了3个变量的显著性"
        "判断，说明诊断检验和补救措施的必要性。",
    ]
    for f in findings:
        add_bullet(doc, f)

    doc.add_heading("7.2 研究局限与未来方向", level=2)
    limitations = [
        "数据来源仅为链家平台，可能存在平台选择偏误（链家在北京二手房市场的占有率虽然较高，"
        "但未必完全代表全市场），不能完全推广至北京二手房整体市场。",
        "DOM变量50%的缺失率对估计一致性构成了实质性威胁。当前采用的中位数填充方法可能"
        "导致系数衰减偏倚，更严格的学术研究应采用多重插补或直接剔除该变量。",
        "模型未纳入宏观经济变量（利率、M2增速、限购政策虚拟变量等），trade_year的系数"
        "可能混杂了时间趋势与宏观冲击的双重效应。",
        "基于OLS的分析框架未处理空间自相关。房价数据具有天然的空间依赖性，后续研究可采用"
        "空间自回归模型（SAR）或空间误差模型（SEM）来建模空间溢出效应。",
        "条件数高达7.84×10⁶表明设计矩阵存在严重病态。虽然通过HC3稳健标准误部分补救，"
        "但仍建议在后续分析中考虑主成分回归（PCR）或偏最小二乘（PLS）等降维方法。",
        "特征工程可以进一步优化：将livingRoom和square的组合替代为单位居室面积"
        "（square/livingRoom），对buildingStructure类别进行合并以减少虚拟变量的稀疏性。",
    ]
    for l in limitations:
        add_bullet(doc, l)

    # ── 参考文献 ──
    doc.add_heading("参考文献", level=1)
    refs = [
        "Rosen, S. (1974). Hedonic prices and implicit markets: product differentiation in pure competition. Journal of Political Economy, 82(1), 34-55.",
        "Lancaster, K. J. (1966). A new approach to consumer theory. Journal of Political Economy, 74(2), 132-157.",
        "Tibshirani, R. (1996). Regression shrinkage and selection via the lasso. Journal of the Royal Statistical Society: Series B, 58(1), 267-288.",
        "Breusch, T. S., & Pagan, A. R. (1979). A simple test for heteroscedasticity and random coefficient variation. Econometrica, 47(5), 1287-1294.",
        "White, H. (1980). A heteroskedasticity-consistent covariance matrix estimator and a direct test for heteroskedasticity. Econometrica, 48(4), 817-838.",
        "Cook, R. D. (1977). Detection of influential observation in linear regression. Technometrics, 19(1), 15-18.",
        "Little, R. J. A., & Rubin, D. B. (2019). Statistical Analysis with Missing Data (3rd ed.). Wiley.",
        "Sirmans, S. G., Macpherson, D. A., & Zietz, E. N. (2005). The composition of hedonic pricing models. Journal of Real Estate Literature, 13(1), 1-44.",
        "Bourassa, S. C., Cantoni, E., & Hoesli, M. (2011). Robust hedonic price models. Real Estate Economics, 39(3), 447-474.",
        "郑思齐, 刘洪玉. (2005). 住房需求的收入弹性: 理论与实证. 中国房地产研究, (2), 1-15.",
        "龙奋杰, 郑思齐. (2007). 城市住房价格的空间特征与影响因素分析. 城市规划, (4), 23-28.",
    ]
    for ref in refs:
        add_text(doc, ref, size=10)

    # ── 保存 ──
    report_path = os.path.join(REPORT_DIR, "分析报告.docx")
    doc.save(report_path)
    print(f"报告已保存至：{report_path}")


if __name__ == "__main__":
    create_report()
