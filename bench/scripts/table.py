"""把 pabiao.json + rivals.json 拼成报告里的总表（Markdown），打印出来。"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
import score as SC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ANS = json.loads((ROOT / "answers.json").read_text(encoding="utf-8"))
PBN = sys.argv[1] if len(sys.argv) > 1 else "pabiao"          # pabiao_before = 第一次比；pabiao = 线上最后一轮
PB = json.loads((ROOT / "out" / f"{PBN}.json").read_text(encoding="utf-8"))
RV = json.loads((ROOT / "out" / "rivals.json").read_text(encoding="utf-8"))
WHO = [("渡表僧", None), ("Nanonets", "nanonets"), ("iLovePDF*", "ilovepdf"), ("PDF24*", "pdf24")]
# 人要动几下：点（不算选文件那一下）/ 等几次 / 登录。照 run_*.py 里真点的步骤数
HANDS = {"渡表僧": "点 1 + 选文件，等 1 次，不登录，Excel 自己下",
         "Nanonets": "点 2 + 选文件，等 1 次，不登录（只给 CSV）",
         "iLovePDF*": "点 2 + 选文件，等 1 次，不登录（OCR 要付费）",
         "PDF24*": "点 3 + 选文件，等 1 次，不登录"}


def get(who, key, f):
    """用磁盘上存下的输出重新评分（评分规则改过也不用重跑浏览器）"""
    r = PB.get(f) if key is None else RV.get(key, {}).get(f)
    if r and "score" in r:
        stem = Path(f).stem
        out = ROOT / "out" / ({"pabiao_before": "pabiao_before"}.get(PBN, "pabiao") if key is None else key)
        path = next(out.glob(stem + ".*"), None)
        if path:
            r = dict(r, score=SC.score(path, f))
    return r


def cell(r):
    if not r:
        return "没比"
    if "score" not in r:
        return "失败"
    s = r["score"]
    pct = 100 * s["body_ok"] / s["body_total"] if s["body_total"] else 0
    extra = f"，标色 {s['wrong_flagged']}" if s.get("wrong_flagged") else ""
    return f"{s['body_ok']}/{s['body_total']}（{pct:.0f}%{extra}）· {r['median']}s"


def main():
    print("| 文件 | 类型 | " + " | ".join(w for w, _ in WHO) + " |")
    print("|---|---|" + "---|" * len(WHO))
    tot = {w: [0, 0] for w, _ in WHO}
    by_kind = {}
    for a in ANS:
        f = a["file"]
        row = [f.split("_")[0] + " " + f.split("_")[1].replace(".pdf", ""), a["kind"]]
        for w, k in WHO:
            r = get(w, k, f)
            row.append(cell(r))
            if r and "score" in r:
                tot[w][0] += r["score"]["body_ok"]
                bk = by_kind.setdefault((a["kind"].split("+")[0], w), [0, 0, []])
                bk[0] += r["score"]["body_ok"]
                bk[2].append(r["median"])
            n = sum(1 for t in a["tables"] for rr in t["rows"] for c in rr if c is not None and "skip" not in c)
            tot[w][1] += n
            bk = by_kind.setdefault((a["kind"].split("+")[0], w), [0, 0, []])
            bk[1] += n
        print("| " + " | ".join(row) + " |")
    ran = {w: any(get(w, k, a["file"]) for a in ANS) for w, k in WHO}
    print("| **合计** | | " + " | ".join(f"**{v[0]}/{v[1]}（{100 * v[0] / v[1]:.0f}%）**" if ran[w] else "要注册，没比" for w, v in tot.items()) + " |")
    print()
    print("| 类型 | " + " | ".join(w for w, _ in WHO) + " |")
    print("|---|" + "---|" * len(WHO))
    for kind in ("有字", "扫描", "拍照"):
        cells = []
        for w, _ in WHO:
            ok, n, secs = by_kind.get((kind, w), [0, 0, []])
            med = sorted(secs)[len(secs) // 2] if secs else "-"
            cells.append(f"{ok}/{n}（{100 * ok / n:.0f}%）· 中位 {med}s" if n and secs else "没比")
        print(f"| {kind} | " + " | ".join(cells) + " |")
    print()
    for w, _ in WHO:
        print(f"- {w}：{HANDS[w]}")


if __name__ == "__main__":
    main()
