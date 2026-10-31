"""造扫描件样本（施工单 010）：samples/o*.pdf + samples/scan_answers.json

三张表（纯英文 / 中文为主 / 中英混排）× 三种质量（300 DPI 端正 / 150 DPI 有点糊 / 仿手机拍照）。
先用 reportlab 画出有字的 PDF，再用 pdfium 渲染成图，糟蹋一下，存成只有图的 PDF。内容全是编的。
用法：.venv/Scripts/python tests/make_scans.py
"""
import io
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageChops, ImageDraw, ImageFilter
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

from make_samples import D, N, S, answer, body_table, money, para, title

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "samples"


# ---------------------------------------------------------------- 三张表（有字的版本，只在内存里）
def table_en(rng):
    head = ["No.", "Part No.", "Description", "Qty", "Unit Price", "Amount", "Due Date"]
    descs = ["Hex bolt M8x30", "Flat washer 8mm", "Bearing 6204-2RS", "O-ring 25x3", "Spindle belt", "Coolant 5L",
             "End mill 8mm", "Copper bush", "Dowel pin 6x24", "Cable tie 200", "Pipe clamp DN25", "Linear rail 300",
             "Timing belt", "Air fitting 1/4"]
    rows = []
    d0 = date(2025, 11, 3)
    for i in range(14):
        code = f"0{rng.randint(1000, 9999)}" if i % 4 != 3 else f"PN-{rng.randint(1000, 9999)}"
        qty = rng.choice([4, 12, 60, 250, 1200, 3000, 15000])
        price = round(rng.uniform(0.2, 480), 2)
        amt = round(qty * price, 2) * (-1 if i in (5, 11) else 1)
        d = d0 + timedelta(days=rng.randint(0, 60))
        rows.append([N(i + 1, str(i + 1)), S(code), S(descs[i]), N(qty, f"{qty:,}"), N(price, f"{price:,.2f}"),
                     N(amt, money(amt)), D(d, d.isoformat())])
    def draw(cv):
        title(cv, 50, 790, "PURCHASE ORDER  PO-2511-0042")
        cv.setFont("Helvetica", 10)
        cv.drawString(50, 768, "Supplier: Example Hardware Co., Ltd.   (test sample, all made up)")
        g = body_table([30, 58, 122, 50, 64, 84, 72], head, rows, "rllrrrl", fs=10, row_h=21)
        g.draw(cv, 40, 745, "all")
        cv.setFont("Helvetica", 10)
        cv.drawString(50, 745 - 21 * 15 - 30, "Approved by: ________     Negative amounts are credit notes.")
    return A4, draw, [answer([head], rows)]


def table_zh(rng):
    head = ["序号", "物料名称", "规格型号", "单位", "数量", "单价", "金额", "备注"]
    names = ["六角螺栓", "平垫圈", "深沟球轴承", "密封圈", "切削液", "立铣刀", "铜套", "联轴器", "定位销", "尼龙扎带",
             "不锈钢管卡", "导轨滑块", "同步带", "气缸接头"]
    specs = ["镀锌八级", "国标加厚", "双面密封", "丁腈橡胶", "水溶性", "四刃涂层", "含油自润", "梅花弹性", "淬火磨光",
             "黑色耐候", "单边加厚", "法兰型", "圆弧齿", "快插直通"]
    units = ["个", "个", "套", "个", "桶", "支", "件", "套", "个", "包", "个", "套", "条", "个"]
    notes = ["", "加急", "", "库存不足", "", "返修", "", "", "供应商缺货", "", "", "样品", "", "下周到"]
    rows = []
    total = 0.0
    for i in range(14):
        qty = rng.choice([2, 8, 20, 50, 120, 600, 2400])
        price = round(rng.uniform(0.5, 900), 2)
        amt = round(qty * price, 2)
        total += amt
        rows.append([N(i + 1, str(i + 1)), S(names[i]), S(specs[i]), S(units[i]), N(qty, f"{qty:,}"),
                     N(price, f"{price:,.2f}"), N(amt, money(amt)), S(notes[i]) if notes[i] else ("", None)])
    total = round(total, 2)
    rows.append([S("合计")] + [("", None)] * 5 + [N(total, money(total)), ("", None)])
    def draw(cv):
        title(cv, 50, 790, "二车间十一月领料汇总表")
        para(cv, 50, 766, ["领料部门：二车间　　制表：示例甲　　（测试样本，内容全是编的）"])
        g = body_table([32, 78, 74, 34, 50, 62, 82, 74], head, rows, "rlllrrrl", fs=10, row_h=22)
        g.draw(cv, 40, 745, "h")
        para(cv, 50, 745 - 22 * 16 - 30, ["审核：示例乙　　仓库：示例丙"])
    return A4, draw, [answer([head], rows)]


def table_mix(rng):
    head = ["编号 Code", "品名 Description", "规格 Spec", "数量 Qty", "单价 Price", "金额 Amount", "变动 Change", "比率 Rate"]
    descs = ["轴承 Bearing", "立铣刀 End mill", "密封圈 O-ring", "导轨 Rail", "主轴 Spindle", "垫片 Gasket",
             "线缆 Cable", "铜套 Bush", "螺栓 Bolt", "气管 Hose", "齿轮 Gear", "销钉 Pin", "滑块 Slider", "夹具 Fixture",
             "法兰 Flange", "弹簧 Spring"]
    specs = ["Φ20×25", "Φ8×60", "Φ25×3", "L300×15", "Φ65×220", "Φ40×2", "2×1.5mm²", "Φ20×25", "M8×30", "Φ6×4",
             "24T×2", "Φ6×24", "15×47", "120×80", "DN50×PN16", "Φ1.2×15"]
    rows = []
    for i in range(16):
        code = f"{rng.randint(1, 99999):06d}"
        qty = rng.choice([1, 12, 250, -12, 3000, -3, 48])
        price = round(rng.uniform(0.5, 2600), 2)
        amt = round(rng.uniform(-80000, 2_500_000), 2)
        amt_shown = money(amt, 2, paren=(i % 2 == 1))
        chg = rng.randint(-9000, 9000)
        rate = round(rng.uniform(-25, 60), 1)
        rows.append([S(code), S(descs[i]), S(specs[i]), N(qty, str(qty)), N(price, f"{price:,.2f}"), N(amt, amt_shown),
                     N(chg, f"{chg:,}"), N(round(rate / 100, 6), f"{rate:.1f}%")])
    W, H = landscape(A4)
    def draw(cv):
        title(cv, 40, H - 46, "Purchase Summary 采购汇总（示例 Sample）", fs=14)
        para(cv, 40, H - 68, ["括号 ( ) 和负号 - 都是负数。编号以 0 开头的照原样保留。"], fs=10)
        g = body_table([62, 128, 82, 58, 72, 98, 72, 62], head, rows, "lllrrrrr", fs=10, row_h=22)
        g.draw(cv, 40, H - 84, "all")
    return (W, H), draw, [answer([head], rows)]


# ---------------------------------------------------------------- 画、渲染、糟蹋
def vector_pdf(size, draw):
    buf = io.BytesIO()
    cv = canvas.Canvas(buf, pagesize=size)
    draw(cv)
    cv.showPage()
    cv.save()
    return buf.getvalue()


def render(pdf_bytes, dpi):
    pdf = pdfium.PdfDocument(pdf_bytes)
    img = pdf[0].render(scale=dpi / 72).to_pil()
    pdf.close()
    return img


def solve(A, b):         # 高斯消元，透视变换系数用
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def perspective_coeffs(dst, src):
    """PIL 要的是「输出点 → 输入点」：dst 是输出图里的四个角，src 是原图里对应的四个角"""
    A, b = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    return solve(A, b)


def as_pdf(img, dpi, path, quality=80):
    img.save(path, "PDF", resolution=float(dpi), quality=quality)


def scan300(img_rng, pdf_bytes, path):
    img = render(pdf_bytes, 300).convert("L")
    noise = Image.effect_noise(img.size, 10)
    img = Image.blend(img, noise, 0.04)
    as_pdf(img, 300, path, quality=85)


def scan150(img_rng, pdf_bytes, path):
    img = render(pdf_bytes, 150).convert("L")
    img = img.rotate(-0.6, resample=Image.BICUBIC, expand=False, fillcolor=255)
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    noise = Image.effect_noise(img.size, 24)
    img = Image.blend(img, noise, 0.08)
    as_pdf(img, 150, path, quality=70)


def photo(img_rng, pdf_bytes, path):
    """仿手机拍照：纸放在桌上，斜着拍（透视 + 歪 2 度），一侧有阴影，偏暖色，有点糊，JPEG 压过"""
    dpi = 200
    page = render(pdf_bytes, dpi).convert("RGB")
    w, h = page.size
    m = int(0.06 * w)                                   # 桌面露出来的边
    W, H = w + 2 * m, h + 2 * m
    # 纸的四个角落在照片里的位置：上边窄、右下角往外撇一点
    dst = [(m + 0.05 * w, m + 0.02 * h), (m + 0.95 * w, m + 0.035 * h), (m + w * 1.01, m + h * 0.99), (m - 0.01 * w, m + h * 0.975)]
    co = perspective_coeffs(dst, [(0, 0), (w, 0), (w, h), (0, h)])
    mask = Image.new("L", page.size, 255).transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC)
    paper = page.transform((W, H), Image.PERSPECTIVE, co, Image.BICUBIC, fillcolor=(255, 255, 255))
    desk = Image.new("RGB", (W, H), (96, 84, 72))
    img = Image.composite(paper, desk, mask)
    img = img.rotate(2.0, resample=Image.BICUBIC, expand=False, fillcolor=(96, 84, 72))
    # 暖色纸 + 阴影：左上亮、右下暗，右边再压一道手机的影子
    shade = Image.new("L", (3, 3))
    shade.putdata([255, 240, 215, 240, 215, 190, 215, 190, 160])
    shade = shade.resize((W, H), Image.BICUBIC)
    hand = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hand).ellipse([int(W * 0.72), int(H * 0.45), int(W * 1.35), int(H * 1.3)], fill=150)
    hand = hand.filter(ImageFilter.GaussianBlur(W * 0.04))
    shade = ImageChops.multiply(shade, hand)
    tint = Image.merge("RGB", [shade.point(lambda v: int(v * 0.98)), shade.point(lambda v: int(v * 0.93)), shade.point(lambda v: int(v * 0.82))])
    img = ImageChops.multiply(img, tint)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    noise = Image.effect_noise((W, H), 30).convert("RGB")
    img = Image.blend(img, noise, 0.05)
    as_pdf(img, dpi, path, quality=78)


def main():
    rng = random.Random(10010)
    answers = []
    tables = [("英文表", table_en), ("中文表", table_zh), ("混排表", table_mix)]
    quals = [("300dpi", scan300), ("150dpi", scan150), ("拍照", photo)]
    k = 0
    for tname, make in tables:
        size, draw, ans = make(rng)
        pdf_bytes = vector_pdf(size, draw)
        for qname, fn in quals:
            k += 1
            path = OUT / f"o{k}_{tname}_{qname}.pdf"
            fn(random.Random(k), pdf_bytes, path)
            answers.append({"file": path.name, "scanned": True, "quality": qname, "tables": ans})
            print(path.name, f"{path.stat().st_size / 1024:.0f} KB")
    (OUT / "scan_answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
