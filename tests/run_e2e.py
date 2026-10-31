"""端到端测试：本机起服务（网页 + 假谷歌），用 Edge 跑每份样本，下载的 Excel 逐格对标准答案。

用法：.venv/Scripts/python tests/run_e2e.py [样本名关键字…] [--no-shots]
结果打印出来，同时写进 tests/out/report.json。截图写进 docs/。
要联网：页面从 cdn.jsdelivr.net 拉 pdf.js 和 ExcelJS（跟线上一样）。
"""
import json
import re
import sys
import threading
import time
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import openpyxl
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
OUT = ROOT / "tests" / "out"
ANSWERS = {a["file"]: a for f in ("answers.json", "scan_answers.json") if (SAMPLES / f).exists()
           for a in json.loads((SAMPLES / f).read_text(encoding="utf-8"))}
FLAG_FILLS = {"FFFFF2CC": "黄", "FFF8CBAD": "橙", "FFFFC7CE": "红"}


def flag_of(cell):
    rgb = cell.fill.fgColor.rgb if cell.fill and cell.fill.fill_type == "solid" else None
    return FLAG_FILLS.get(rgb) if isinstance(rgb, str) else None


# ---------------------------------------------------------------- 假谷歌：按钥匙的开头决定怎么回
class Fake:
    calls = {}
    lock = threading.Lock()

    @classmethod
    def count(cls, key):
        with cls.lock:
            cls.calls[key] = cls.calls.get(key, 0) + 1
            return cls.calls[key]


def truth_tables():
    a = ANSWERS["s6_扫描版.pdf"]["tables"][0]
    return [{"header": [list(h) for h in a["header"]], "rows": [list(r) for r in a["shown"]]}]


def gemini_ok(tables):
    return 200, {"candidates": [{"content": {"parts": [{"text": json.dumps({"tables": tables}, ensure_ascii=False)}],
                                             "role": "model"}, "finishReason": "STOP"}]}


def err(code, status, msg, details=None):
    e = {"code": code, "message": msg, "status": status}
    if details:
        e["details"] = details
    return code, {"error": e}


def quota(per):
    qid = f"GenerateRequestsPer{per}PerProjectPerModel-FreeTier"
    det = [{"@type": "type.googleapis.com/google.rpc.QuotaFailure",
            "violations": [{"quotaMetric": "generativelanguage.googleapis.com/generate_content_free_tier_requests",
                            "quotaId": qid}]}]
    if per == "Minute":
        det.append({"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": "2s"})
    return err(429, "RESOURCE_EXHAUSTED",
               "You exceeded your current quota, please check your plan and billing details. "
               "For more information on this error, head to: https://ai.google.dev/gemini-api/docs/rate-limits.", det)


def fake_answer(model, key):
    if model == "gemini-nope":
        return err(404, "NOT_FOUND", f"models/{model} is not found for API version v1beta, or is not supported for "
                                     "generateContent. Call ListModels to see the list of available models and their "
                                     "supported methods.")
    n = Fake.count(key)
    kind = key.split("_")[0]
    if kind == "bad":
        return err(400, "INVALID_ARGUMENT", "API key not valid. Please pass a valid API key.",
                   [{"@type": "type.googleapis.com/google.rpc.ErrorInfo", "reason": "API_KEY_INVALID",
                     "domain": "googleapis.com"}])
    if kind == "html":
        return 200, "<html><body><h1>502 Bad Gateway</h1></body></html>"
    if kind == "minute" and n == 1:
        return quota("Minute")
    if kind == "day":
        return quota("Day")
    t = truth_tables()
    if kind == "flaky" and n == 2:          # 第二遍认错一格：第三遍当裁判，二比一，不标红
        t[0]["rows"][3][4] = "250"
    if kind == "split":                     # 三遍各认各的：标红
        t[0]["rows"][1][5] = ["59.42", "59.47", "69.42"][(n - 1) % 3]
    return gemini_ok(t)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        u = urlparse(self.path)
        m = re.match(r"^/v1beta/models/([^/:]+):generateContent$", u.path)
        n = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(n)
        if not m:
            self.send_error(404)
            return
        key = parse_qs(u.query).get("key", [""])[0]
        assert "x-goog-api-key" not in {k.lower() for k in self.headers.keys()}, "钥匙只许走 ?key="
        req = json.loads(body)
        assert req["contents"][0]["parts"][1]["inline_data"]["mime_type"] == "image/jpeg"
        code, out = fake_answer(m.group(1), key)
        data = out.encode() if isinstance(out, str) else json.dumps(out, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html" if isinstance(out, str) else "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


# ---------------------------------------------------------------- 对答案
def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip()


def check_cell(exp, got):
    """返回 (类别, 对不对)。类别：num / date / text / empty"""
    if exp is None:
        return "empty", got is None or got == ""
    if "n" in exp:
        ok = isinstance(got, (int, float)) and not isinstance(got, bool) and abs(got - exp["n"]) <= 1e-9 * max(1, abs(exp["n"]))
        return "num", ok
    if "d" in exp:
        return "date", isinstance(got, datetime) and got.date().isoformat() == exp["d"]
    return "text", isinstance(got, str) and norm(got) == norm(exp["s"])


def score(xlsx, ans):
    wb = openpyxl.load_workbook(xlsx)
    sheets = [ws for ws in wb.worksheets if ws.title != "扒表记录"]
    rep = {"tables_expected": len(ans["tables"]), "tables_got": len(sheets), "tables": []}
    tot = {"num": [0, 0], "date": [0, 0], "text": [0, 0], "empty": [0, 0], "header": [0, 0]}
    zeros = [0, 0]
    sums_ok = True
    miss = {"num_flagged": 0, "num_silent": 0, "text_flagged": 0, "text_silent": 0}
    silent = []
    for i, t in enumerate(ans["tables"]):
        tr = {"rows_expected": len(t["rows"]), "wrong": []}
        if i >= len(sheets):
            tr["missing"] = True
            for row in t["rows"]:
                for e in row:
                    k = "empty" if e is None else ("num" if "n" in e else "date" if "d" in e else "text")
                    tot[k][1] += 1
            rep["tables"].append(tr)
            continue
        ws = sheets[i]
        H = len(t["header"])
        ncols = len(t["header"][0])
        tr["sheet"] = ws.title
        tr["rows_got"] = ws.max_row - H
        tr["cols_got"] = ws.max_column
        tr["cols_expected"] = ncols
        for r, hrow in enumerate(t["header"]):
            for c, e in enumerate(hrow):
                got = ws.cell(r + 1, c + 1).value
                ok = (e is None and got in (None, "")) or (e is not None and isinstance(got, str) and norm(got) == norm(e))
                tot["header"][0] += ok
                tot["header"][1] += 1
                if not ok:
                    tr["wrong"].append(f"表头 {ws.cell(r + 1, c + 1).coordinate}: 应为 {e!r} 实为 {got!r}")
        got_merges = sorted(str(m) for m in ws.merged_cells.ranges)
        exp_merges = sorted(f"{openpyxl.utils.get_column_letter(m[1] + 1)}{m[0] + 1}:{openpyxl.utils.get_column_letter(m[3] + 1)}{m[2] + 1}"
                            for m in t["merges"])
        tr["merges_ok"] = [m for m in got_merges if int(re.sub(r"\D", "", m.split(":")[0])) <= H] == exp_merges
        if not tr["merges_ok"]:
            tr["wrong"].append(f"合并：应为 {exp_merges} 实为 {got_merges}")
        colsum_e, colsum_g = {}, {}
        for r, row in enumerate(t["rows"]):
            for c, e in enumerate(row):
                got = ws.cell(H + r + 1, c + 1).value
                k, ok = check_cell(e, got)
                tot[k][0] += ok
                tot[k][1] += 1
                if e is not None and "s" in e and re.fullmatch(r"0\d+", e["s"]):
                    zeros[1] += 1
                    zeros[0] += got == e["s"]
                if e is not None and "n" in e:
                    colsum_e[c] = colsum_e.get(c, 0) + e["n"]
                    if isinstance(got, (int, float)):
                        colsum_g[c] = colsum_g.get(c, 0) + got
                if not ok:
                    fl = flag_of(ws.cell(H + r + 1, c + 1))
                    kind = "num" if k in ("num", "date") else "text"
                    miss[f"{kind}_{'flagged' if fl else 'silent'}"] += 1
                    if kind == "num" and not fl:
                        silent.append(f"{ws.cell(H + r + 1, c + 1).coordinate}: 应为 {e} 实为 {got!r}")
                    if len(tr["wrong"]) < 40:
                        tr["wrong"].append(f"{ws.cell(H + r + 1, c + 1).coordinate}: 应为 {e} 实为 {got!r}" + (f" [{fl}]" if fl else " [没标]"))
        for c in colsum_e:
            if abs(colsum_e[c] - colsum_g.get(c, 0)) > 1e-6 * max(1, abs(colsum_e[c])):
                sums_ok = False
        extra = ws.max_row - H - len(t["rows"])
        if extra > 0:
            tr["wrong"].append(f"多出 {extra} 行")
        rep["tables"].append(tr)
    rep["cells"] = {k: f"{v[0]}/{v[1]}" for k, v in tot.items()}
    rep["num_wrong"] = tot["num"][1] - tot["num"][0] + tot["date"][1] - tot["date"][0]
    rep["text_wrong"] = tot["text"][1] - tot["text"][0] + tot["empty"][1] - tot["empty"][0]
    rep["header_wrong"] = tot["header"][1] - tot["header"][0]
    rep["leading_zero"] = f"{zeros[0]}/{zeros[1]}"
    rep["column_sums_ok"] = sums_ok
    rep["wrong_flagged"] = miss
    rep["silent_num"] = silent[:20]
    rep["flags_total"] = sum(1 for ws in sheets for row in ws.iter_rows() for c in row if flag_of(c))
    return rep


# ---------------------------------------------------------------- 样本 8：Edge「打印成 PDF」导出（字体嵌子集，像 Word / 网页导出的真文件）
# 里面嵌了系统字体的子集，所以不进仓库：每次测试现造，放 tests/out/
def make_s8(browser):
    import random
    rng = random.Random(8008)
    shops = ["一车间", "二车间", "三车间", "装配线 A", "装配线 B", "外协 Outsource"]
    a_rows, a_html = [], []
    for name in shops:
        plan = rng.randint(800, 30000)
        real = rng.randint(int(plan * 0.7), int(plan * 1.1))
        rate = round(real / plan * 100, 1)
        a_rows.append([{"s": name}, {"n": plan}, {"n": real}, {"n": round(rate / 100, 6)}])
        a_html.append(f"<tr><td>{name}</td><td class=r>{plan:,}</td><td class=r>{real:,}</td><td class=r>{rate:.1f}%</td></tr>")
    b_rows, b_html = [], []
    goods = ["铝合金支架 Bracket A", "不锈钢垫片", "电机座 Motor Base", "导轨 Rail 300", "外壳", "齿轮 24T"]
    for i in range(70):
        d = f"2025-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        code = f"{rng.randint(0, 999999):06d}"
        g = rng.choice(goods)
        q = rng.randint(1, 9000)
        amt = round(rng.uniform(-30000, 300000), 2)
        shown = f"({abs(amt):,.2f})" if amt < 0 else f"{amt:,.2f}"
        note = rng.choice(["", "", "加急", "返修 Rework", ""])
        b_rows.append([{"d": d}, {"s": code}, {"s": g}, {"n": q}, {"n": amt}, ({"s": note} if note else None)])
        b_html.append(f"<tr><td>{d}</td><td>{code}</td><td>{g}</td><td class=r>{q:,}</td><td class=r>{shown}</td><td>{note}</td></tr>")
    html = f"""<!doctype html><meta charset=utf-8><style>
      body{{font-family:'Microsoft YaHei',sans-serif;font-size:10pt;margin:0}} h1{{font-size:16pt}}
      table{{border-collapse:collapse;margin:10pt 0}} td,th{{padding:3pt 8pt}} .r{{text-align:right}}
      table.a td,table.a th{{border:0.75pt solid #333}} table.b thead th{{border-bottom:1pt solid #000;text-align:left}}
      table.b th.r{{text-align:right}}</style>
      <h1>月度生产与出货（示例，网页导出）</h1><p>下表为各车间产量达成情况，数据为虚构。</p>
      <table class=a><thead><tr><th rowspan=2>车间</th><th colspan=2>产量（件）</th><th rowspan=2>达成率</th></tr>
      <tr><th>计划</th><th>实际</th></tr></thead><tbody>{''.join(a_html)}</tbody></table>
      <p>出货明细如下，负数金额为退货冲减。备注为空表示正常。</p>
      <table class=b><thead><tr><th>日期</th><th>料号</th><th>品名</th><th class=r>数量</th><th class=r>金额</th><th>备注</th></tr></thead>
      <tbody>{''.join(b_html)}</tbody></table><p>以上。</p>"""
    OUT.mkdir(parents=True, exist_ok=True)
    pdf = OUT / "s8_网页导出.pdf"
    pg = browser.new_page()
    pg.set_content(html)
    pg.pdf(path=str(pdf), format="A4", margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"})
    pg.close()
    ANSWERS[pdf.name] = {"file": pdf.name, "tables": [
        {"header": [["车间", "产量（件）", None, "达成率"], [None, "计划", "实际", None]],
         "merges": [[0, 0, 1, 0], [0, 1, 0, 2], [0, 3, 1, 3]], "rows": a_rows},
        {"header": [["日期", "料号", "品名", "数量", "金额", "备注"]], "merges": [], "rows": b_rows}]}
    return pdf


# ---------------------------------------------------------------- 跑浏览器
def open_page(ctx, port, keys=None, model=None, extra=""):
    page = ctx.new_page()
    if keys is not None or model:
        page.add_init_script(
            f"localStorage.setItem('pabiao.keys', {json.dumps(json.dumps(keys or []))});"
            + f"localStorage.setItem('pabiao.model', {json.dumps(model or 'gemini-3.5-flash-lite')});")
    if "api=" not in extra:                  # 默认走假谷歌，别打到真谷歌去
        extra += f"&api=http://127.0.0.1:{port}/v1beta"
    page.goto(f"http://127.0.0.1:{port}/index.html?fast=1{extra}")
    page.wait_for_function("window.__pabiao && window.__pabiao.ready")
    # 量主线程卡不卡：每 50ms 记一次，看最长隔了多久
    page.evaluate("""() => { const T = window.__pabiao; T.maxGap = 0; let last = performance.now();
        setInterval(() => { const n = performance.now(); T.maxGap = Math.max(T.maxGap, n - last); last = n; }, 50); }""")
    return page


def run_file(page, pdf, expect_download=True, timeout=300_000):
    t0 = time.time()
    dl = None
    if expect_download:
        with page.expect_download(timeout=timeout) as d:
            page.set_input_files("#pick", str(pdf))
        dl = d.value
    else:
        page.set_input_files("#pick", str(pdf))
    page.wait_for_function("window.__pabiao.phase === 'done' && window.__pabiao.result", timeout=timeout)
    secs = time.time() - t0
    res = page.evaluate("window.__pabiao.result")
    res["seconds"] = round(secs, 1)
    res["max_main_thread_gap_ms"] = round(page.evaluate("window.__pabiao.maxGap"))
    res["downloads"] = page.evaluate("window.__pabiao.downloads || 0")
    res["err_text"] = page.inner_text("#d-err") if page.is_visible("#d-err") else ""
    res["key_box"] = page.is_visible("#d-key")
    path = None
    if dl:
        OUT.mkdir(parents=True, exist_ok=True)
        path = OUT / (pdf.stem + ".xlsx")
        dl.save_as(str(path))
    return res, path


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    shots = "--no-shots" not in sys.argv
    srv, port = serve()
    report = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        ctx = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})

        def todo(name):
            return not want or any(w in name for w in want)

        if todo("s8"):
            pdf = make_s8(browser)
            page = open_page(ctx, port)
            res, path = run_file(page, pdf)
            res["score"] = score(path, ANSWERS[pdf.name])
            report[pdf.name] = res
            print(pdf.name, json.dumps(res, ensure_ascii=False, indent=1))
            page.close()

        # 有文字层的样本
        for f in ["s1_简单表.pdf", "s2_跨页表.pdf", "s3_一页多表.pdf", "s4_合并表头.pdf", "s5_中英混排数字.pdf", "s7_66页大文件.pdf"]:
            if not todo(f):
                continue
            page = open_page(ctx, port)
            res, path = run_file(page, SAMPLES / f)
            res["score"] = score(path, ANSWERS[f])
            report[f] = res
            print(f, json.dumps(res, ensure_ascii=False, indent=1))
            if shots and f.startswith("s4"):
                page.screenshot(path=str(ROOT / "docs" / "截图_电脑.png"), full_page=True)
            page.close()

        if todo("edge"):
            # 没有表的纯文字 PDF：不能吐空表，要把正文按行给出来
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            from reportlab.pdfgen import canvas
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            OUT.mkdir(parents=True, exist_ok=True)
            txt = OUT / "e1_没有表.pdf"
            cv = canvas.Canvas(str(txt))
            cv.setFont("STSong-Light", 11)
            for i, ln in enumerate(["关于下周停电检修的通知", "各车间：", "下周六 8:00 至 17:00 全厂停电检修，请提前安排。",
                                    "如有疑问，联系设备科。", "设备科  2025 年 10 月 30 日"]):
                cv.drawString(60, 760 - i * 22, ln)
            cv.showPage()
            cv.save()
            page = open_page(ctx, port)
            res, path = run_file(page, txt)
            wb = openpyxl.load_workbook(path)
            res["sheets"] = wb.sheetnames
            res["fulltext_rows"] = sum(1 for r in wb["扒表记录"].iter_rows(values_only=True) if r[0] and "停电" in str(r[0]))
            report["边角 · 没有表"] = res
            print("没有表", json.dumps(res, ensure_ascii=False))
            page.close()
            bad = OUT / "e2_不是PDF.txt"
            bad.write_text("hello", encoding="utf-8")
            page = open_page(ctx, port)
            res, _ = run_file(page, bad, expect_download=False, timeout=30_000)
            res["err_text"] = page.inner_text("#d-err")
            report["边角 · 不是 PDF"] = res
            print("不是PDF", json.dumps(res, ensure_ascii=False))
            page.close()

        if todo("s6") or todo("gemini"):
            s6 = SAMPLES / "s6_扫描版.pdf"
            # 没钥匙：本地认字，照样出 Excel，人不用多点一下；页面说一句「本地认的」，钥匙框留着
            page = open_page(ctx, port, keys=[])
            res, path = run_file(page, s6, timeout=600_000)
            res["score"] = score(path, ANSWERS["s6_扫描版.pdf"])
            report["s6 没钥匙（本地认）"] = res
            print("s6 没钥匙", json.dumps(res, ensure_ascii=False))
            if shots:
                page.screenshot(path=str(ROOT / "docs" / "截图_扫描件_电脑.png"), full_page=True)
            # 再贴钥匙：借（假）谷歌重认一遍，Excel 再下一次
            with page.expect_download(timeout=120_000) as d:
                page.fill("#d-keyin", "ok_" + "A" * 36)
            page.wait_for_function("window.__pabiao.phase === 'done' && window.__pabiao.result && window.__pabiao.result.via.every(v => v[1] === 'gemini')")
            path = OUT / "s6_扫描版_贴钥匙.xlsx"
            d.value.save_as(str(path))
            res = page.evaluate("window.__pabiao.result")
            res["score"] = score(path, ANSWERS["s6_扫描版.pdf"])
            report["s6 贴钥匙后（谷歌认）"] = res
            print("s6 贴钥匙后", json.dumps(res, ensure_ascii=False))
            page.close()

            # (名字, 钥匙/模型, 期望走谁, 日志或报错里要有的字)
            cases = [
                ("额度到顶（每分钟）", dict(keys=["minute_" + "A" * 30]), "gemini", "每分钟次数到顶"),
                ("额度到顶（当天，换 2 号钥匙）", dict(keys=["day_" + "A" * 30, "ok2_" + "A" * 30]), "gemini", "今天的额度用完了"),
                ("钥匙无效 → 本地认", dict(keys=["bad_" + "A" * 30]), "local", "HTTP 400：API key not valid. Please pass a valid API key."),
                ("模型不存在 → 本地认", dict(keys=["ok3_" + "A" * 30], model="gemini-nope"), "local", "HTTP 404：models/gemini-nope is not found"),
                ("回来的不是 JSON → 本地认", dict(keys=["html_" + "A" * 30]), "local", "返回的不是 JSON：<html>"),
                ("断网 → 本地认", dict(keys=["ok4_" + "A" * 30], extra="&api=http://127.0.0.1:9/v1beta"), "local", "网络错误："),
                ("两把钥匙当天都用完 → 本地认", dict(keys=["day_" + "B" * 30, "day_" + "C" * 30]), "local", "所有钥匙今天的额度都用完了"),
                ("第二遍认错一格（二比一）", dict(keys=["flaky_" + "A" * 30]), "gemini", ""),
                ("三遍各不一样（标红）", dict(keys=["split_" + "A" * 30]), "gemini", ""),
            ]
            for name, kw, via, needle in cases:
                page = open_page(ctx, port, keys=kw["keys"], model=kw.get("model"), extra=kw.get("extra", ""))
                res, path = run_file(page, s6, timeout=600_000)
                log = page.evaluate("window.__pabiao.log")
                res["needle_found"] = (not needle) or any(needle in x for x in log) or needle in res["err_text"]
                res["via_ok"] = all(v[1] == via for v in res["via"])
                if path:
                    res["score"] = score(path, ANSWERS["s6_扫描版.pdf"])
                report["假谷歌 · " + name] = res
                print(name, json.dumps(res, ensure_ascii=False))
                page.close()

        if todo("ocr") or todo("o"):
            # 扫描件本地认字：每份样本电脑宽、手机宽各跑一遍；第一次要下多少、第二次还下不下
            fresh = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})
            got = {"bytes": 0, "files": {}}

            def on_resp(r):
                u = r.url
                if any(k in u for k in ("onnxruntime-web", "models/ppocrv5")):
                    try:
                        n = r.request.sizes()["responseBodySize"]
                    except Exception:
                        n = 0
                    got["bytes"] += n
                    got["files"][u.split("/")[-1]] = n
            fresh.on("response", on_resp)
            files = sorted(f for f, a in ANSWERS.items() if a.get("scanned") and f.startswith("o")) + ["s6_扫描版.pdf"]
            files = [f for f in files if not want or any(w in f for w in want) or "ocr" in want]
            first = None
            for k, f in enumerate(files):
                page = open_page(fresh, port, keys=[])
                res, path = run_file(page, SAMPLES / f, timeout=600_000)
                if k == 0:
                    first = {"bytes": got["bytes"], "files": dict(got["files"])}
                    got["bytes"] = 0
                    got["files"] = {}
                res["score"] = score(path, ANSWERS[f])
                res["ocr"] = page.evaluate("window.__pabiao.ocr")
                page.close()
                report["本地认 · " + f] = res
                print(f, json.dumps({k2: res[k2] for k2 in ("seconds", "title", "max_main_thread_gap_ms", "downloads")}, ensure_ascii=False),
                      json.dumps(res["score"]["cells"], ensure_ascii=False), json.dumps(res["score"]["wrong_flagged"], ensure_ascii=False))
            report["本地认 · 下载量"] = {"第一次": first, "之后（同一个浏览器）": dict(got)}
            print("下载量", json.dumps(report["本地认 · 下载量"], ensure_ascii=False))
            fresh.close()
            mob = browser.new_context(accept_downloads=True, viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                      is_mobile=True, has_touch=True)
            for f in files:
                page = open_page(mob, port, keys=[])
                res, path = run_file(page, SAMPLES / f, timeout=600_000)
                res["score"] = score(path, ANSWERS[f])
                page.close()
                report["本地认 · 手机宽 · " + f] = res
                print("手机宽", f, res["seconds"], json.dumps(res["score"]["cells"], ensure_ascii=False))
            mob.close()

        if shots and todo("s4"):
            m = browser.new_context(accept_downloads=True, viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                    is_mobile=True, has_touch=True)
            page = open_page(m, port)
            page.screenshot(path=str(ROOT / "docs" / "截图_手机_首页.png"))
            run_file(page, SAMPLES / "s4_合并表头.pdf")
            page.screenshot(path=str(ROOT / "docs" / "截图_手机.png"), full_page=True)
            m.close()
            page = open_page(ctx, port)
            page.screenshot(path=str(ROOT / "docs" / "截图_电脑_首页.png"))
            page.close()
        browser.close()
    srv.shutdown()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
