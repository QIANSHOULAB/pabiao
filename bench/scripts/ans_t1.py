"""t1 格力合并资产负债表：文本层拆行 → 答案，再拿合计行核平。"""
import json
import re
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "files" / "t1_格力2024合并资产负债表.pdf"
# 只有一个数的行：数落在哪一列（看页面图定的）
ONLY_LAST = {"衍生金融资产", "应收票据"}

doc = pdfium.PdfDocument(str(PDF))
rows = []
for i in range(len(doc)):
    lines = doc[i].get_textpage().get_text_range().replace("\r", "").split("\n")
    start = next(k for k, l in enumerate(lines) if l.startswith("项 目")) + 1
    for l in lines[start:]:
        if l.startswith("法定代表人"):
            break
        nums = re.findall(r"-?[\d,]+\.\d\d", l)
        rest = l
        for n in nums:
            rest = rest.replace(n, "")
        m = re.search(r"五、\d+", rest)
        note = m.group(0) if m else None
        label = (rest.replace(note, "") if note else rest).strip()
        vals = [float(n.replace(",", "")) for n in nums]
        if len(vals) == 1:
            vals = [None, vals[0]] if label in ONLY_LAST else [vals[0], None]
        elif not vals:
            vals = [None, None]
        rows.append([label, note, *vals])

# 核平：合计 = 上面明细之和（「其中」行不算）
def chk(total, items):
    by = {r[0]: r for r in rows}
    for c in (2, 3):
        s = sum(by[k][c] or 0 for k in items)
        t = by[total][c]
        assert abs(s - t) < 0.005, (total, c, s, t)
    print("核平", total)

labels = [r[0] for r in rows]
def between(a, b, skip=()):
    i, j = labels.index(a), labels.index(b)
    return [labels[k] for k in range(i + 1, j) if labels[k] not in skip and not labels[k].endswith("：")]

SUB = {"其中：应收利息", "应收股利", "其中：应付利息", "应付股利", "其中：优先股", "永续债"}
chk("流动资产合计", between("流动资产：", "流动资产合计", SUB))
chk("非流动资产合计", between("非流动资产：", "非流动资产合计", SUB))
chk("流动负债合计", between("流动负债：", "流动负债合计", SUB))
chk("非流动负债合计", between("非流动负债：", "非流动负债合计", SUB))
by = {r[0]: r for r in rows}
for c in (2, 3):  # 库存股是减项
    s = sum(by[k][c] or 0 for k in between("股东权益：", "归属于母公司股东权益合计", SUB) if k != "减：库存股")
    assert abs(s - by["减：库存股"][c] - by["归属于母公司股东权益合计"][c]) < 0.005
print("核平 归属于母公司股东权益合计")
for c in (2, 3):
    assert abs(by["流动资产合计"][c] + by["非流动资产合计"][c] - by["资产总计"][c]) < 0.005
    assert abs(by["流动负债合计"][c] + by["非流动负债合计"][c] - by["负债合计"][c]) < 0.005
    assert abs(by["归属于母公司股东权益合计"][c] + by["少数股东权益"][c] - by["股东权益合计"][c]) < 0.005
    assert abs(by["负债合计"][c] + by["股东权益合计"][c] - by["负债和股东权益总计"][c]) < 0.005
    assert abs(by["资产总计"][c] - by["负债和股东权益总计"][c]) < 0.005
print("总计核平；行数", len(rows))

def cell(v):
    if v is None or v == "":
        return None
    return {"n": v} if isinstance(v, float) else {"s": v}

ans = {"file": PDF.name, "kind": "有字", "tables": [{
    "header": [["项 目", "附注", "2024 年 12 月 31 日", "2024 年 1 月 1 日"]], "merges": [],
    "rows": [[cell(x) for x in r] for r in rows]}]}
out = ROOT / "out" / "ans_t1.json"
out.write_text(json.dumps(ans, ensure_ascii=False, indent=1), encoding="utf-8")
print(out)
