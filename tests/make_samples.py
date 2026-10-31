"""造样本 PDF 和标准答案：samples/*.pdf + samples/answers.json

全是编的：公司、客户、物料都是瞎起的名字，不碰任何真文件。固定随机种子，每次造出来一模一样。
用法：.venv/Scripts/python tests/make_samples.py
"""
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

from PIL import Image, ImageFilter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples"
pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))   # 不嵌字体，靠 CMap：正好考 pdf.js 的 cMapUrl
CJK = "STSong-Light"
LAT = "Helvetica"


# ---------------------------------------------------------------- 格子的值：(显示的字, 标准答案)
def S(text):
    return (text, {"s": text})


def N(value, shown):
    return (shown, {"n": value})


def D(d, shown):
    return (shown, {"d": d.isoformat()})


def money(v, dec=2, paren=False):
    s = f"{abs(v):,.{dec}f}"
    if v < 0:
        return f"({s})" if paren else f"-{s}"
    return s


def is_cjk(text):
    return any(ord(ch) > 0x2E7F for ch in text)


def font_for(text):
    return CJK if is_cjk(text) else LAT


# ---------------------------------------------------------------- 画表
class Grid:
    """cells: [(r, c, rs, cs, shown, align, bold)]；按行高、列宽摆好，画线方式 lines = 'all' | 'h' | 'head' | None"""

    def __init__(self, widths, row_h=18, fs=9):
        self.widths, self.row_h, self.fs = widths, row_h, fs
        self.cells = []

    def add(self, r, c, shown, align="l", rs=1, cs=1, bold=False):
        self.cells.append((r, c, rs, cs, shown, align, bold))

    def nrows(self):
        return max(r + rs for r, c, rs, cs, *_ in self.cells)

    def draw(self, cv, x0, ytop, lines="all", head_rows=1, cmid=()):
        xs = [x0]
        for w in self.widths:
            xs.append(xs[-1] + w)
        n = self.nrows()
        ys = [ytop - i * self.row_h for i in range(n + 1)]
        cv.setLineWidth(0.6)
        for r, c, rs, cs, shown, align, bold in self.cells:
            left, right = xs[c], xs[c + cs]
            top, bottom = ys[r], ys[r + rs]
            if lines == "all":
                cv.rect(left, bottom, right - left, top - bottom, stroke=1, fill=0)
            if shown == "":
                continue
            f = font_for(shown)
            if bold and f == LAT:
                f = "Helvetica-Bold"
            cv.setFont(f, self.fs)
            base = (top + bottom) / 2 - self.fs * 0.35
            if align == "r":
                cv.drawRightString(right - 4, base, shown)
            elif align == "c":
                cv.drawCentredString((left + right) / 2, base, shown)
            else:
                cv.drawString(left + 4, base, shown)
        if lines in ("h", "head"):
            if lines == "h":
                cv.setLineWidth(1.0)
                cv.line(xs[0], ys[0], xs[-1], ys[0])
                cv.line(xs[0], ys[-1], xs[-1], ys[-1])
            cv.setLineWidth(0.6)
            cv.line(xs[0], ys[head_rows], xs[-1], ys[head_rows])
            for (r, c1, c2) in cmid:
                cv.line(xs[c1] + 3, ys[r], xs[c2 + 1] - 3, ys[r])
        return ys[-1]


def para(cv, x, y, lines, fs=10.5, lead=16):
    cv.setFont(CJK, fs)
    for ln in lines:
        cv.drawString(x, y, ln)
        y -= lead
    return y


def title(cv, x, y, text, fs=15):
    cv.setFont(CJK, fs)
    cv.drawString(x, y, text)


def footer(cv, page, total, w=A4[0]):
    cv.setFont(CJK, 8)
    cv.drawCentredString(w / 2, 28, f"第 {page} 页 / 共 {total} 页")


def body_table(widths, head, rows, aligns, fs=9, row_h=18):
    """单行表头 + 表身。rows 里每格是 (显示, 答案)"""
    g = Grid(widths, row_h, fs)
    for c, h in enumerate(head):
        g.add(0, c, h, "c", bold=True)
    for r, row in enumerate(rows, 1):
        for c, (shown, _) in enumerate(row):
            g.add(r, c, shown, aligns[c])
    return g


def answer(head_rows, rows, merges=()):
    return {"header": head_rows, "merges": [list(m) for m in merges], "rows": [[a for _, a in row] for row in rows],
            "shown": [[sh for sh, _ in row] for row in rows]}   # 印在纸上的样子：假谷歌照这个回


# ---------------------------------------------------------------- 样本 1：一页一张简单的表（有格线）
def s1(rng):
    path = OUT / "s1_简单表.pdf"
    cv = canvas.Canvas(str(path), pagesize=A4)
    title(cv, 50, 790, "示例五金厂 · 十月领料单")
    para(cv, 50, 765, ["领料部门：二车间　　单据编号：LL-2510-017　　（本单为测试样本，内容全是编的）"])
    names = ["六角螺栓", "平垫圈", "弹簧垫圈", "内六角螺钉", "铝合金支架", "密封圈", "轴承 6204", "定位销",
             "不锈钢管卡", "尼龙扎带", "铜套", "联轴器"]
    specs = ["M8×30", "Φ8", "Φ10", "M6×20", "AL-40", "O-25×3", "6204-2RS", "Φ6×24", "DN25", "4×200", "Φ20×25", "D30"]
    rows, total = [], 0.0
    for i in range(12):
        code = f"{rng.randint(0, 9999):06d}" if i % 3 != 2 else f"A-{rng.randint(1000, 9999)}"
        qty = rng.choice([5, 12, 40, 100, 250, 1200, 3000])
        price = round(rng.uniform(0.3, 380), 2)
        amt = round(qty * price, 2)
        total += amt
        rows.append([N(i + 1, str(i + 1)), S(code), S(names[i]), S(specs[i]), N(qty, f"{qty:,}"),
                     N(price, f"{price:.2f}"), N(amt, money(amt))])
    total = round(total, 2)
    rows.append([S("合计"), S(""), S(""), S(""), S(""), S(""), N(total, money(total))])
    rows[-1] = [rows[-1][0]] + [("", None)] * 5 + [rows[-1][6]]
    head = ["序号", "零件号", "名称", "规格", "数量", "单价（元）", "金额（元）"]
    g = body_table([36, 62, 92, 72, 56, 76, 96], head, rows, "rlllrrr")
    g.draw(cv, 50, 745, "all")
    para(cv, 50, 745 - 18 * 14 - 30, ["领料人：示例甲　　审核：示例乙"])
    cv.showPage()
    cv.save()
    return {"file": path.name, "tables": [answer([head], rows)]}


# ---------------------------------------------------------------- 样本 2：一张表跨 4 页，表头只印在第一页（没有竖线）
def s2(rng):
    path = OUT / "s2_跨页表.pdf"
    cv = canvas.Canvas(str(path), pagesize=A4)
    head = ["日期", "单号", "客户", "品名", "数量", "金额", "毛利率"]
    widths = [64, 92, 70, 120, 46, 70, 46]
    aligns = "llllrrr"
    clients = ["甲方精密", "乙丙五金", "丁戊电子", "己庚塑胶", "辛壬模具"]
    goods = ["铝合金支架 Bracket-A", "不锈钢垫片 Shim-08", "电机座 Motor Base", "导轨 Rail-300", "外壳 Housing-B",
             "齿轮 Gear-24T"]
    rows = []
    d0 = date(2025, 7, 1)
    for i in range(118):
        d = d0 + timedelta(days=i * 92 // 118)
        no = f"SO-{d:%y%m%d}-{i % 7 + 1:02d}"
        qty = rng.choice([60, 120, 480, 1200, 2400, 15000])
        amt = round(qty * rng.uniform(1.2, 58), 2)
        gm = round(rng.uniform(-4, 36), 1)
        rows.append([D(d, d.isoformat()), S(no), S(rng.choice(clients)), S(rng.choice(goods)),
                     N(qty, f"{qty:,}"), N(amt, money(amt)), N(round(gm / 100, 4), f"{gm:.1f}%")])
    per = [34, 40, 40, 4]
    total_pages = 4
    k = 0
    for p in range(total_pages):
        if p == 0:
            title(cv, 50, 790, "2025 年三季度出货明细")
            para(cv, 50, 766, ["统计口径：按出库日期。金额单位：元。"], fs=9.5)
            ytop = 740
        else:
            ytop = 800
        g = Grid(widths, 17, 8.5)
        r0 = 0
        if p == 0:
            for c, h in enumerate(head):
                g.add(0, c, h, "l" if c < 4 else "r", bold=True)
            r0 = 1
        chunk = rows[k:k + per[p]]
        k += per[p]
        for r, row in enumerate(chunk, r0):
            for c, (shown, _) in enumerate(row):
                g.add(r, c, shown, aligns[c])
        yb = g.draw(cv, 50, ytop, "head" if p == 0 else None, head_rows=1)
        if p == total_pages - 1:
            para(cv, 50, yb - 30, ["以上数据为测试样本，客户名称均为虚构。", "制表：示例部门"], fs=9.5)
        footer(cv, p + 1, total_pages)
        cv.showPage()
    cv.save()
    assert k == len(rows)
    return {"file": path.name, "tables": [answer([head], rows)]}


# ---------------------------------------------------------------- 样本 3：一页三张表，中间夹着正文
def s3(rng):
    path = OUT / "s3_一页多表.pdf"
    cv = canvas.Canvas(str(path), pagesize=A4)
    title(cv, 50, 790, "车间周报（第 43 周，示例）")
    y = para(cv, 50, 764, ["本周三个班组照常排产，夜班因换模停机两次。以下是各班组的产量和不良率，",
                            "数字来自 MES 导出，未经财务复核。"])
    tA_head = ["班组", "产量（件）", "不良率"]
    tA = []
    for name in ["早班 A", "早班 B", "中班", "夜班"]:
        q = rng.randint(800, 20000)
        bad = round(rng.uniform(0.2, 4.8), 2)
        tA.append([S(name), N(q, f"{q:,}"), N(round(bad / 100, 6), f"{bad:.2f}%")])
    g = body_table([90, 90, 80], tA_head, tA, "lrr")
    y = g.draw(cv, 50, y - 8, "all") - 26
    y = para(cv, 50, y, ["机台方面，VM-07 主轴报警一次，已更换编码器线。停机明细如下："])
    tB_head = ["机台", "开机时长（h）", "停机次数", "备注"]
    tB = [[S("VM-07"), N(142.5, "142.5"), N(2, "2"), S("主轴报警")],
          [S("4X-9"), N(160, "160.0"), N(0, "0"), S("正常")],
          [S("CNC-12"), N(98.25, "98.25"), N(5, "5"), S("等料 Waiting")],
          [S("LT-3"), N(0, "0.0"), N(1, "1"), S("保养")]]
    g = body_table([70, 90, 66, 110], tB_head, tB, "lrrl")
    y = g.draw(cv, 50, y - 8, "head") - 26
    y = para(cv, 50, y, ["费用部分：退料冲减用括号表示负数。"])
    tC_head = ["项目", "金额（元）"]
    tC = [[S("刀具"), N(12850.0, "12,850.00")], [S("润滑油"), N(1320.5, "1,320.50")],
          [S("退料冲减"), N(-1200.0, "(1,200.00)")], [S("合计"), N(12970.5, "12,970.50")]]
    g = body_table([110, 100], tC_head, tC, "lr")
    y = g.draw(cv, 50, y - 8, "all") - 26
    para(cv, 50, y, ["下周计划：夜班恢复双机台，目标不良率 1.5% 以下。"])
    cv.showPage()
    cv.save()
    return {"file": path.name, "tables": [answer([tA_head], tA), answer([tB_head], tB), answer([tC_head], tC)]}


# ---------------------------------------------------------------- 样本 4：表头有合并单元格（一张有格线，一张只有横线）
def s4(rng):
    path = OUT / "s4_合并表头.pdf"
    cv = canvas.Canvas(str(path), pagesize=A4)
    title(cv, 50, 790, "区域销售汇总（示例）")
    g = Grid([70, 70, 70, 70, 70, 80], 20, 9)
    g.add(0, 0, "地区", "c", rs=2, bold=True)
    g.add(0, 1, "2025 年销售额（万元）", "c", cs=4, bold=True)
    g.add(0, 5, "全年合计", "c", rs=2, bold=True)
    for c, q in enumerate(["Q1", "Q2", "Q3", "Q4"], 1):
        g.add(1, c, q, "c", bold=True)
    rows = []
    for r, area in enumerate(["华东", "华南", "华北", "西南", "东北", "海外 Overseas"], 2):
        qs = [round(rng.uniform(80, 2600), 1) for _ in range(4)]
        tot = round(sum(qs), 1)
        row = [S(area)] + [N(v, f"{v:,.1f}") for v in qs] + [N(tot, f"{tot:,.1f}")]
        rows.append(row)
        for c, (shown, _) in enumerate(row):
            g.add(r, c, shown, "l" if c == 0 else "r")
    y = g.draw(cv, 50, 760, "all") - 34
    head1 = [["地区", "2025 年销售额（万元）", None, None, None, "全年合计"], [None, "Q1", "Q2", "Q3", "Q4", None]]
    m1 = [(0, 0, 1, 0), (0, 1, 0, 4), (0, 5, 1, 5)]

    para(cv, 50, y, ["产品计划完成情况（只有横线的三线表）："])
    g = Grid([110, 70, 70, 70, 70], 18, 9)
    g.add(0, 0, "产品", "l", rs=2, bold=True)
    g.add(0, 1, "2024", "c", cs=2, bold=True)
    g.add(0, 3, "2025", "c", cs=2, bold=True)
    for c, h in enumerate(["实际", "计划", "实际", "计划"], 1):
        g.add(1, c, h, "r", bold=True)
    rows2 = []
    for r, prod in enumerate(["齿轮箱 GB-1", "电机座", "导轨 Rail", "外壳 Housing", "支架"], 2):
        vals = [rng.randint(300, 98000) for _ in range(4)]
        row = [S(prod)] + [N(v, f"{v:,}") for v in vals]
        rows2.append(row)
        for c, (shown, _) in enumerate(row):
            g.add(r, c, shown, "l" if c == 0 else "r")
    g.draw(cv, 50, y - 10, "h", head_rows=2, cmid=[(1, 1, 2), (1, 3, 4)])
    head2 = [["产品", "2024", None, "2025", None], [None, "实际", "计划", "实际", "计划"]]
    m2 = [(0, 0, 1, 0), (0, 1, 0, 2), (0, 3, 0, 4)]
    cv.showPage()
    cv.save()
    return {"file": path.name, "tables": [answer(head1, rows, m1), answer(head2, rows2, m2)]}


# ---------------------------------------------------------------- 样本 5：中英混排、各种数字写法（两页，第二页重印表头）
def s5(rng):
    path = OUT / "s5_中英混排数字.pdf"
    W, H = landscape(A4)
    cv = canvas.Canvas(str(path), pagesize=(W, H))
    head = ["Item 编号", "Description 描述", "Date 日期", "Qty", "Amount 金额", "Change 变动", "Rate 比率"]
    widths = [70, 170, 92, 50, 100, 90, 66]
    descs = ["Hex bolt 六角螺栓", "Bearing 轴承 6204", "O-ring 密封圈", "Spindle 主轴", "Coolant 切削液 5L",
             "End mill 立铣刀 Φ8", "Gasket 垫片", "Cable 线缆 2m"]
    rows = []
    for i in range(30):
        code = rng.choice([f"{rng.randint(1, 999):04d}", f"{rng.randint(1, 9999):05d}", f"{rng.randint(1, 99999):06d}",
                           f"P{rng.randint(100, 999)}"])
        d = date(2025, 1, 1) + timedelta(days=rng.randint(0, 360))
        style = i % 3
        dshown = [d.isoformat(), f"{d.year}/{d.month}/{d.day}", f"{d.year}年{d.month}月{d.day}日"][style]
        qty = rng.choice([1, 12, 250, -12, 3000, -3])
        amt = round(rng.uniform(-50000, 2_500_000), 2)
        dec = 0 if i % 2 == 0 else 2
        chg = round(rng.uniform(-9000, 9000), dec)
        chg_shown = money(chg, dec, paren=True)
        rate = round(rng.uniform(-20, 60), i % 2)
        rate_shown = f"{rate:.{i % 2}f}%"
        rate = round(rate / 100, 6)
        rows.append([S(code), S(rng.choice(descs)), D(d, dshown), N(qty, str(qty)), N(amt, money(amt)),
                     N(chg, chg_shown), N(rate, rate_shown)])
    per = [19, 11]
    k = 0
    for p in range(2):
        title(cv, 40, H - 44, "Purchase Summary 采购汇总（示例 Sample）" + ("" if p == 0 else "（续）"), fs=13)
        g = body_table(widths, head, rows[k:k + per[p]], "lllrrrr", fs=8.5, row_h=19)
        g.draw(cv, 40, H - 64, "all")
        k += per[p]
        footer(cv, p + 1, 2, W)
        cv.showPage()
    cv.save()
    return {"file": path.name, "tables": [answer([head], rows)]}


# ---------------------------------------------------------------- 样本 7：66 页大文件，每页重印表头（没有线）
def s7(rng):
    path = OUT / "s7_66页大文件.pdf"
    cv = canvas.Canvas(str(path), pagesize=A4)
    head = ["序号", "物料编码", "物料名称", "仓位", "库存", "单价", "金额"]
    widths = [40, 70, 130, 60, 60, 64, 86]
    names = ["六角螺栓 M8", "平垫圈 Φ8", "轴承 6204", "密封圈 O-25", "导轨 Rail-300", "齿轮 24T", "铜套 Φ20",
             "立铣刀 Φ8", "切削液 5L", "尼龙扎带", "定位销 Φ6", "电机座"]
    rows = []
    pages, per = 66, 45
    for i in range(pages * per):
        code = f"{rng.randint(0, 99999999):08d}"
        stock = rng.randint(0, 50000)
        price = round(rng.uniform(0.05, 900), 2)
        amt = round(stock * price, 2)
        rows.append([N(i + 1, str(i + 1)), S(code), S(rng.choice(names)), S(f"{rng.choice('ABCDE')}-{rng.randint(1, 40):02d}"),
                     N(stock, f"{stock:,}"), N(price, f"{price:,.2f}"), N(amt, money(amt))])
    for p in range(pages):
        cv.setFont(CJK, 8)
        cv.drawString(50, 812, "库存盘点表（示例）")
        g = body_table(widths, head, rows[p * per:(p + 1) * per], "rllrrrr", fs=8, row_h=16)
        g.draw(cv, 50, 795, None)
        footer(cv, p + 1, pages)
        cv.showPage()
    cv.save()
    return {"file": path.name, "tables": [answer([head], rows)]}


# ---------------------------------------------------------------- 样本 6：扫描版（把样本 1 转成图片，歪 1.2 度，加噪点）
def s6(ans1):
    import pypdfium2 as pdfium
    src = OUT / "s1_简单表.pdf"
    path = OUT / "s6_扫描版.pdf"
    pdf = pdfium.PdfDocument(str(src))
    img = pdf[0].render(scale=200 / 72).to_pil().convert("L")
    pdf.close()
    img = img.rotate(-1.2, resample=Image.BICUBIC, expand=False, fillcolor=255)
    noise = Image.effect_noise(img.size, 28)
    img = Image.blend(img, noise, 0.12).filter(ImageFilter.GaussianBlur(0.6))
    img.save(path, "PDF", resolution=200.0)
    return {"file": path.name, "scanned": True, "tables": ans1["tables"]}


def main():
    OUT.mkdir(exist_ok=True)
    rng = random.Random(9009)
    answers = []
    a1 = s1(rng)
    answers.append(a1)
    answers.append(s2(rng))
    answers.append(s3(rng))
    answers.append(s4(rng))
    answers.append(s5(rng))
    answers.append(s6(a1))
    answers.append(s7(rng))
    (OUT / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=1), encoding="utf-8")
    for a in answers:
        n = sum(len(t["rows"]) for t in a["tables"])
        print(f"{a['file']}: {len(a['tables'])} 张表, {n} 行")


if __name__ == "__main__":
    main()
