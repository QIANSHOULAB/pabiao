"""标准答案原稿：对着页面图逐格录，录完跑一遍，合计核平才写进 bench/answers.json。
格式照 samples/answers.json：{"n":数} {"s":字} {"d":"YYYY-MM-DD"} 或 None。另加 kind：有字 / 扫描 / 拍照。"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N = lambda v: {"n": v}
S = lambda v: {"s": v}
ALL = []


def add(file, kind, tables):
    ALL.append({"file": file, "kind": kind, "tables": tables})


def near(a, b, tol):
    assert abs(a - b) <= tol, (a, b)


# ---------------------------------------------------------------- t1 格力：文本层生成，ans_t1.py 已核平
t1 = json.loads((ROOT / "out" / "ans_t1.json").read_text(encoding="utf-8"))
add(t1["file"], "有字", t1["tables"])

# ---------------------------------------------------------------- t2 香港就业行业分布（第 14 页，两张表）
t2 = [
    ("製造", "Manufacturing", 2.3, 2.1, 2.1),
    ("電力及燃氣供應", "Electricity and gas supply", 0.2, 0.2, 0.2),
    ("自來水供應；污水處理、廢棄物管理及污染防治服務",
     "Water supply; sewerage, waste management and remediation services", 0.2, 0.2, 0.2),
    ("建造", "Construction", 8.4, 9.5, 9.1),
    ("進出口貿易", "Import and export trade", 10.7, 9.2, 8.8),
    ("批發", "Wholesale", 1.4, 1.2, 1.2),
    ("零售", "Retail", 7.7, 7.0, 6.8),
    ("運輸、倉庫、郵政及速遞服務", "Transportation, storage, postal and courier services", 7.9, 7.8, 7.9),
    ("住宿及膳食服務", "Accommodation and food services", 6.4, 6.7, 6.7),
    ("資訊及通訊", "Information and communications", 3.0, 3.0, 3.0),
    ("金融及保險", "Financing and insurance", 7.5, 7.2, 7.4),
    ("地產", "Real estate", 4.0, 4.1, 4.3),
    ("專業、科學及技術服務", "Professional, scientific and technical services", 5.6, 5.8, 5.9),
    ("行政及支援服務", "Administrative and support services", 5.5, 5.4, 5.4),
    ("公共行政", "Public administration", 3.3, 3.6, 3.5),
    ("教育", "Education", 6.0, 6.2, 6.3),
    ("人類保健及社會工作服務", "Human health and social work services", 5.9, 6.5, 6.7),
    ("藝術、娛樂及康樂活動", "Arts, entertainment and recreation", 1.4, 1.5, 1.5),
    ("其他社會及個人服務", "Other social and personal services", 12.6, 12.6, 13.0),
    ("其他", "Others", 0.1, 0.1, 0.1),
]
for c in (2, 3, 4):  # 百分比四舍五入，合计允许差 0.3
    near(sum(r[c] for r in t2), 100.0, 0.3)
t2_rows = [[S(a), S(b), N(x), N(y), N(z)] for a, b, x, y, z in t2]
t2_rows += [[S("所有行業主類"), S("All industry sections"), N(100.0), N(100.0), N(100.0)],
            [S("總就業人數（千人）"), S("Total employment ('000)"), N(3691.7), N(3694.7), N(3674.0)],
            [None, None, N(-4.7), N(-0.4), N(-0.6)]]
near(  # 括号里是同比：2025 那格能用上一年核
(3674.0 / 3694.7 - 1) * 100, -0.6, 0.05)
add("t2_香港就业行业分布.pdf", "有字", [
    {"header": [["行業主類", "Industry section", "2020", "2024", "2025@"]], "merges": [], "rows": t2_rows},
    {"header": [[None, None, "2020", "2024", "2025"]], "merges": [],
     "rows": [[S("公務員人數（千人）"), S("Number of civil servants ('000)"), N(177.0), N(172.6), N(170.6)],
              [None, None, N(-0.2), S("(§)"), N(-1.2)]]}])
near((170.6 / 172.6 - 1) * 100, -1.2, 0.05)

# ---------------------------------------------------------------- t3 美国 2020 普查分州人口（文本层生成，合计核平）
txt = (ROOT / "out" / "census.txt").read_text(encoding="utf-8").splitlines()
st = []
for l in txt:
    m = re.fullmatch(r"(.+?) ([\d,]{6,})", l.strip())
    if m:
        st.append((m.group(1), int(m.group(2).replace(",", ""))))
names = [s for s, _ in st]
i_tot = names.index("TOTAL RESIDENT POPULATION1")
assert i_tot == 51, i_tot
assert sum(v for _, v in st[:51]) == st[51][1]
assert st[51][1] + st[52][1] == st[53][1]
t3_rows = [[S("TOTAL RESIDENT POPULATION" if s == "TOTAL RESIDENT POPULATION1" else s), N(v)] for s, v in st]
add("t3_美国2020普查分州人口.pdf", "有字", [
    {"header": [["AREA", "RESIDENT POPULATION (APRIL 1, 2020)"]], "merges": [], "rows": t3_rows}])

# ---------------------------------------------------------------- t4 格力第 26 页：分行业/产品/地区 + 营业成本构成
P = lambda v: N(round(v / 100, 6))   # 百分数照 samples 的规矩存小数：32.55% → 0.3255
a = [("分行业",), ("制造业", 169715353002.47, 114476752530.27, 32.55, -2.78, -1.17, -1.09),
     ("其他业务", 19448301062.17, 19019367093.09, 2.21, -33.88, -32.36, -2.20), ("分产品",),
     ("消费电器", 148559931838.58, 96691946304.39, 34.91, -4.29, -3.34, -0.65),
     ("其他业务", 19448301062.17, 19019367093.09, 2.21, -33.88, -32.36, -2.20), ("分地区",),
     ("内销-主营业务", 141512822056.59, 93045292807.84, 34.25, -5.45, -3.93, -1.04),
     ("外销-主营业务", 28202530945.88, 21431459722.43, 24.01, 13.25, 12.86, 0.26),
     ("其他业务", 19448301062.17, 19019367093.09, 2.21, -33.88, -32.36, -2.20)]
for r in a:
    if len(r) > 1:
        near((1 - r[2] / r[1]) * 100, r[3], 0.006)
near(a[7][1] + a[8][1], a[1][1], 0.005)
near(a[7][2] + a[8][2], a[1][2], 0.005)
b = [("家电制造", "原材料", 93363351952.22, 86.05, 93909272081.72, 86.13, -0.58),
     (None, "人工成本", 4879947485.74, 4.50, 4839203936.92, 4.44, 0.84),
     (None, "折旧", 1759556442.08, 1.62, 1950717636.85, 1.79, -9.80),
     (None, "能源", 1131053297.69, 1.04, 1060398535.08, 0.97, 6.66)]
for r in b:
    near((r[2] / r[4] - 1) * 100, r[6], 0.006)
near(b[0][2] / b[0][3], b[1][2] / b[1][3], 0.002 * b[0][2] / b[0][3])   # 各项占比推出的总成本一致
add("t4_格力2024分产品收入与成本构成.pdf", "有字", [
    {"header": [["项目", "营业收入", "营业成本", "毛利率", "营业收入比上年同期增减", "营业成本比上年同期增减", "毛利率比上年同期增减"]],
     "merges": [],
     "rows": [[S(r[0])] + [None] * 6 if len(r) == 1 else [S(r[0]), N(r[1]), N(r[2])] + [P(v) for v in r[3:]] for r in a]},
    {"header": [["行业分类", "项目", "2024 年", None, "2023 年", None, "同比增减"],
                [None, None, "金额", "占营业成本比重", "金额", "占营业成本比重", None]],
     "merges": [[0, 0, 1, 0], [0, 1, 1, 1], [0, 2, 0, 3], [0, 4, 0, 5], [0, 6, 1, 6]],
     "rows": [[None if r[0] is None else S(r[0]), S(r[1]), N(r[2]), P(r[3]), N(r[4]), P(r[5]), P(r[6])] for r in b]}])

# ---------------------------------------------------------------- t5 Superior Plus 样本发票（发票是页里的一张图，右边说明是文字层）
add("t5_SuperiorPlus样本发票.pdf", "有字+图", [
    {"header": [["DATE", "GALLONS", "PRODUCT", "TICKET#", "PPG", "TOTAL"]], "merges": [],
     "rows": [[{"d": "2017-02-15"}, N(520.9), S("Propane"), S("555555"), S("@ $0.4000"), N(999.99)],
              [S("Total Invoice"), None, None, None, None, N(999.99)]]}])

# ---------------------------------------------------------------- s1 1937 美国统计摘要 No.135（扫描，左右两半并排）
L = [("Total", 165315, 70183980), None, ("Arizona", 6185, 2961864), ("Arkansas", 4, 1600),
     ("California", 8453, 3418768), ("Colorado", 20905, 8374157), ("Idaho", 7786, 3550358),
     ("Kansas", 233, 58506), ("Michigan", 5, 1821), ("Minnesota", 1, 75), ("Montana", 21295, 7707511)]
R = [("Nebraska", 585, 108313), ("Nevada", 930, 493757), ("New Mexico", 34102, 15582904),
     ("North Dakota", 939, 288918), ("Oklahoma", 366, 71349), ("Oregon", 8272, 3372682),
     ("South Dakota", 7952, 2730220), ("Utah", 5110, 2779167), ("Washington", 1599, 513589),
     ("Wyoming", 40435, 18144574), ("General Land Office", 158, 23847)]
for c in (1, 2):
    assert sum(r[c] for r in L[2:]) + sum(r[c] for r in R) == L[0][c], c
side = lambda r: [None, None, None] if r is None else [S(r[0]), N(r[1]), N(r[2])]
add("s1_美国统计摘要1937_表135.pdf", "扫描", [
    {"header": [["State", "Entries", "Acres", "State", "Entries", "Acres"]], "merges": [],
     "rows": [side(a) + side(b) for a, b in zip(L, R)]}])

# ---------------------------------------------------------------- s2 1937 美国统计摘要 No.303（扫描）
Y = ["1900", "1910", "1920", "1930", "1933", "1934", "1935"]
t303 = [
    ("Number of companies", 76, 214, 272, 352, 318, 313, 340),
    ("Capital stock, Dec. 31", 12832, 40545, 66905, 176943, 149353, 147944, 148748),
    ("Income, total", 400603, 781011, 1764213, 4593973, 4622292, 4785985, 5072095),
    ("Premium income, total", 324724, 593388, 1384939, 3524327, 3321798, 3520984, 3692128),
    ("New premiums", 62276, 70180, 274478, 385067, 240077, 290849, 359398),
    ("Renewals", 256142, 517536, 1099740, 3031537, 2816384, 2816001, 2822207),
    ("Annuities", 6306, 5672, 10721, 107723, 265337, 414134, 510523),
    ("Interest and other income, total", 75879, 187623, 379274, 1069646, 1300494, 1265001, 1379968),
    ("Interest, dividends, etc", 64949, 160514, 324370, 853188, 824436, 861305, 876030),
    ("Rents", 8225, 10310, 16312, 37292, 62902, 99715, 137004),
    ("Other", 2706, 16799, 38592, 179166, 413156, 303980, 366933),
]
for c in range(1, 8):  # 原书单位千美元、各项分别四舍五入：1900、1934、1935 有 ±1，数字放大逐位核过
    near(t303[3][c], t303[4][c] + t303[5][c] + t303[6][c], 1)
    near(t303[7][c], t303[8][c] + t303[9][c] + t303[10][c], 1)
    near(t303[2][c], t303[3][c] + t303[7][c], 1)
add("s2_美国统计摘要1937_表303.pdf", "扫描", [
    {"header": [[None] + Y], "merges": [], "rows": [[S(r[0])] + [N(v) for v in r[1:]] for r in t303]}])

# ---------------------------------------------------------------- s3 1961 统计汇编 表24、表32（扫描，繁体）
t24 = [("總數", 742, 2254, 100.0, 100.0), ("100名以下", 319, 1274, 43.0, 56.5), ("101—500名", 287, 645, 38.7, 28.6),
       ("501—1000名", 89, 182, 12.0, 8.1), ("1001—2000名", 38, 92, 5.1, 4.1), ("2001—3000名", 6, 29, 0.8, 1.3),
       ("3001名以上", 3, 32, 0.4, 1.4)]
for c in (1, 2):
    assert sum(r[c] for r in t24[1:]) == t24[0][c]
for c in (3, 4):
    near(sum(r[c] for r in t24[1:]), 100.0, 0.05)
B = lambda v: S(v) if isinstance(v, str) else N(v)
t32 = [("平壤市", 100, 43, 261, 964, 992, "23倍", 379), ("平安南道", 100, 59, 170, 502, 635, "11倍", 374),
       ("平安北道", 100, 212, 330, 740, 948, 448, 287), ("慈江道", 100, 345, 851, "22倍", "26倍", 748, 303),
       ("黃海南道", 100, 100.1, 124, 768, "11倍", "11倍", 853), ("黃海北道", 100, 26, 73, 378, 424, "16倍", 582),
       ("江原道", 100, 16, 75, 249, 342, "21倍", 454), ("咸鏡南道", 100, 36, 117, 299, 350, 984, 299),
       ("咸鏡北道", 100, 73, 211, 540, 677, 928, 317), ("兩江道", 100, 62, 327, 627, 666, "11倍", 204),
       ("開城市", None, 100, 651, "33倍", "37倍", "—", 563)]
pct = lambda v: v if isinstance(v, (int, float)) else int(v[:-1]) * 100   # 都换成百分数，「23倍」= 2300
for r in t32:  # 后两列 = 1960 ÷ 1953、1960 ÷ 1956（「×倍」只精确到倍，容差 12%）
    assert abs(pct(r[5]) / r[3] * 100 - pct(r[7])) / pct(r[7]) < 0.12, r
    if r[6] != "—":
        assert abs(pct(r[5]) / pct(r[2]) * 100 - pct(r[6])) / pct(r[6]) < 0.12, r
add("s3_朝鲜统计汇编1961_表24表32.pdf", "扫描", [
    {"header": [[None, "企業數（所）", None, "比重（%）", None], [None, "1954", "1960", "1954", "1960"]],
     "merges": [[0, 0, 1, 0], [0, 1, 0, 2], [0, 3, 0, 4]],
     "rows": [[S(r[0])] + [N(v) for v in r[1:]] for r in t24]},
    {"header": [[None, "1949", "1953", "1956", "1959", "1960", "1960", "1960"],
                [None, None, None, None, None, None, "1953", "1956"]],
     "merges": [[0, c, 1, c] for c in range(6)],
     "rows": [[S(r[0])] + [None if v is None else B(v) for v in r[1:]] for r in t32]}])

# ---------------------------------------------------------------- p1 地拉那公交时刻表（拍照）
# 第三组第三行中间有个糊掉的字（像「7.00 ö- 20.00」），人也认不准：那格不计分，记成 {"skip": …}
G = ["5.30 - 6.00", "6.00 - 7.00", "7.00 - 20.00", "20.00 - 22.00", "22.00 - 24.00"]
p1 = [[S(G[0]), S("Çdo 6 min"), S("5.00 - 6.00"), S("Çdo 6 min"), S("5.00/5.30 - 6.00"), S("Çdo 7 min")],
      [S(G[1]), S("Çdo 5 min"), S(G[1]), S("Çdo 5 min"), S(G[1]), S("Çdo 6 min")],
      [S(G[2]), S("Çdo 4 min"), S(G[2]), S("Çdo 4 min"), {"skip": "7.00 ?- 20.00"}, S("Çdo 5 min")],
      [S(G[3]), S("Çdo 6 min"), S(G[3]), S("Çdo 6 min"), S(G[3]), S("Çdo 7 min")],
      [S(G[4]), S("Çdo 8 min"), S(G[4]), S("Çdo 8 min"), S(G[4]), S("Çdo 8 min")]]
T = "LINJA QYTETËSE PER TRANSPORT UDHËTAR UNAZA"
add("p1_地拉那公交时刻表_拍照.pdf", "拍照", [
    {"header": [[T] + [None] * 5, [T] + [None] * 5, ["FREKUENCAT"] + [None] * 5,
                ["nëntor - mars", None, "prill - tetor", None, "ditë pushimi dhe festa", None],
                ["ora", "frekuenca"] * 3],
     "merges": [[0, 0, 0, 5], [1, 0, 1, 5], [2, 0, 2, 5], [3, 0, 3, 1], [3, 2, 3, 3], [3, 4, 3, 5]],
     "rows": p1}])

if __name__ == "__main__":
    out = ROOT / "answers.json"
    out.write_text(json.dumps(ALL, ensure_ascii=False, indent=1), encoding="utf-8")
    for a in ALL:
        cells = sum(1 for t in a["tables"] for r in t["rows"] for c in r if c is not None)
        print(a["file"], a["kind"], "表", len(a["tables"]), "非空格", cells)
