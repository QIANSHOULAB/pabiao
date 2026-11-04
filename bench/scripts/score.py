"""比武评分：任何一家吐出来的 xlsx / csv，跟 bench/answers.json 逐格比。各家用同一个办法。

对齐办法（报告里也写了）：
  1. 把这家输出的每张工作表当成一个网格（渡表僧的「扒表记录」页是日志，不算）。
  2. 一张答案表 = 表头行 + 数据行。在所有工作表上试所有整表平移（行偏移 × 列偏移），
     挑「还没对上的数据格」对上最多的那个位置，记下这一块对上的行。
  3. 剩下没对上的行再找下一块，直到一块里对上的格子少于 2 个。表被拆成几张、中间少一行后面整体错位，都靠这一步接上。
  4. 最后还没对上的数据行，整行算错。
  只数答案里非空的格；{"skip":…} 的格（人也认不准）不算。表头另算，不进「准」。

一格算对：
  数：输出能读成同一个数就对。认 1,234 / 1 234 / (1,234)=负数 / (-4.7) / 32.55%=0.3255 / 末尾的脚注记号 * @ §；
      百分数存成 32.55 还是 0.3255 都算对。
  日期：Excel 日期，或写成 2/15/2017、2017-02-15 的字。
  字：去掉所有空白、统一大小写、各种横杠当成一样、几个繁简字折叠，去掉末尾的脚注记号后相同就对；两边都能读成同一个数也算对。
用法：score.py 输出文件 文件名(answers.json 里的 file)   → 打印 JSON
"""
import csv
import json
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANSWERS = {a["file"]: a for a in json.loads((ROOT / "answers.json").read_text(encoding="utf-8"))}
FLAG_FILLS = {"FFFFF2CC": "黄", "FFF8CBAD": "橙", "FFFFC7CE": "红"}
FOLD = str.maketrans("黃鏡兩開國營業數類總銷產電務價際資負債錢額區劃統計會樂藝衛運倉庫郵遞訊險專學術個處應氣廢棄汙戶齊衆這來華灣門歲準屬權鈔幣", "黄镜两开国营业数类总销产电务价际资负债钱额区划统计会乐艺卫运仓库邮递讯险专学术个处应气废弃污户齐众这来华湾门岁准属权钞币")   # 只折几个常见繁简字，两边一起折
DASH = re.compile(r"[—–‐‑‒―－一~～-]+")
FOOT = re.compile(r"(\(\d\)|[¹²³⁴⁵⁶⁷⁸⁹⁰*@§†‡])+$")


def load(path):
    """→ [(表名, 网格 [[值]], 颜色 [[黄/橙/红/None]])]"""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        raw = path.read_bytes()
        for enc in ("utf-8-sig", "gb18030", "latin-1"):
            try:
                txt = raw.decode(enc)
                break
            except UnicodeDecodeError:
                pass
        rows = list(csv.reader(txt.splitlines()))
        return [(path.stem, [[c if c != "" else None for c in r] for r in rows], None)]
    import openpyxl
    wb = openpyxl.load_workbook(path, data_only=True)
    out = []
    for ws in wb.worksheets:
        if ws.title in ("扒表记录", "Log"):
            continue
        g, f = [], []
        for row in ws.iter_rows():
            g.append([c.value for c in row])
            fl = []
            for c in row:
                rgb = c.fill.fgColor.rgb if c.fill and c.fill.fill_type == "solid" else None
                fl.append(FLAG_FILLS.get(rgb) if isinstance(rgb, str) else None)
            f.append(fl)
        out.append((ws.title, g, f))
    return out


def ntext(s):
    s = unicodedata.normalize("NFKC", str(s))      # PDF 文字层常用兼容区汉字（力=U+F98A），长得一样
    s = re.sub(r"\s+", "", s).casefold().translate(FOLD)
    s = DASH.sub("-", s)
    s = FOOT.sub("", s)
    s = re.sub(r"(?<=[a-z])\d$", "", s)          # POPULATION1 这种脚注
    return s


def num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"\s+", "", str(v))
    s = FOOT.sub("", s).replace(",", "").replace("$", "").replace("¥", "").replace("@", "").replace("￥", "")
    neg = False
    m = re.fullmatch(r"\((.+)\)", s)
    if m:
        s = m.group(1)
        neg = not s.startswith("-")
    pct = s.endswith("%")
    s = s.rstrip("%")
    s = s.replace("−", "-")
    if not re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
        return None
    x = float(s) * (-1 if neg else 1)
    return x / 100 if pct else x


def close(a, b):
    return abs(a - b) <= 1e-6 * max(1.0, abs(b))


def as_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                pass
    return None


def match(exp, got):
    if got is None or got == "":
        return False
    if "n" in exp:
        p = num(got)
        e = exp["n"]
        return p is not None and (close(p, e) or close(p, e * 100) or close(p, e / 100))
    if "d" in exp:
        d = as_date(got)
        return d is not None and d.isoformat() == exp["d"]
    if ntext(got) == ntext(exp["s"]):
        return True
    a, b = num(got), num(exp["s"])
    return a is not None and b is not None and close(a, b)


def scored(e):
    return e is not None and "skip" not in e


def best_block(sheets, grid, todo):
    """在所有表、所有平移里，找对上 todo 行里最多格子的位置。"""
    best = (0, None)
    ncol = max(len(r) for r in grid)
    for si, (_, g, _) in enumerate(sheets):
        if not g:
            continue
        gw = max((len(r) for r in g), default=0)
        for dr in range(-len(grid) + 1, len(g)):
            rows = [i for i in todo if 0 <= i + dr < len(g)]
            for dc in range(-ncol + 1, gw):
                hit = 0
                for i in rows:
                    gr = g[i + dr]
                    for j, e in enumerate(grid[i]):
                        if scored(e) and 0 <= j + dc < len(gr) and match(e, gr[j + dc]):
                            hit += 1
                if hit > best[0]:
                    best = (hit, (si, dr, dc))
    return best


def score(path, file):
    ans = ANSWERS[file]
    sheets = load(path)
    out = {"sheets": len(sheets), "sheet_shapes": [(n, len(g), max((len(r) for r in g), default=0)) for n, g, _ in sheets],
           "tables": []}
    tot = {"body": [0, 0], "header": [0, 0], "wrong_flagged": 0, "wrong_silent": 0, "flags_on_right": 0}
    for t in ans["tables"]:
        H = len(t["header"])
        grid = [[None if h is None else {"s": h} for h in hr] for hr in t["header"]] + t["rows"]
        body = set(range(H, len(grid)))
        todo = set(range(len(grid)))
        blocks, got_of = [], {}
        while todo & body:
            hit, pos = best_block(sheets, grid, sorted(todo))
            if hit < 2:
                break
            si, dr, dc = pos
            g = sheets[si][1]
            covered = []
            for i in sorted(todo):
                if not 0 <= i + dr < len(g):
                    continue
                gr = g[i + dr]
                if any(scored(e) and 0 <= j + dc < len(gr) and match(e, gr[j + dc]) for j, e in enumerate(grid[i])):
                    covered.append(i)
                    got_of[i] = (si, i + dr, dc)
            todo -= set(covered)
            blocks.append({"sheet": sheets[si][0], "row_shift": dr, "col_shift": dc, "rows": len(covered)})
        tr = {"blocks": blocks, "wrong": []}
        for i, row in enumerate(grid):
            for j, e in enumerate(row):
                if not scored(e):
                    continue
                k = "header" if i < H else "body"
                tot[k][1] += 1
                got, flag = None, None
                if i in got_of:
                    si, r, dc = got_of[i]
                    g, fl = sheets[si][1], sheets[si][2]
                    if 0 <= j + dc < len(g[r]):
                        got = g[r][j + dc]
                        flag = fl[r][j + dc] if fl else None
                ok = match(e, got)
                tot[k][0] += ok
                if k == "body" and ok and flag:
                    tot["flags_on_right"] += 1
                if k == "body" and not ok:
                    tot["wrong_flagged" if flag else "wrong_silent"] += 1
                    if len(tr["wrong"]) < 30:
                        tr["wrong"].append(f"r{i - H + 1}c{j + 1}: 应为 {list(e.values())[0]!r} 实为 {got!r}" + (f" [{flag}]" if flag else ""))
        tr["rows_unmatched"] = len(todo & body)
        out["tables"].append(tr)
    out["body"] = f"{tot['body'][0]}/{tot['body'][1]}"
    out["body_ok"], out["body_total"] = tot["body"]
    out["header"] = f"{tot['header'][0]}/{tot['header'][1]}"
    out["wrong_flagged"], out["wrong_silent"], out["flags_on_right"] = tot["wrong_flagged"], tot["wrong_silent"], tot["flags_on_right"]
    return out


if __name__ == "__main__":
    print(json.dumps(score(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=1))
