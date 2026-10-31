"""开发用：扫描件本地认字，逐份对答案，打印认错的格子。

用法：.venv/Scripts/python tests/dev_ocr.py [样本名关键字…] [--engine tess] [--debug]
"""
import json
import sys

from playwright.sync_api import sync_playwright

from run_e2e import ANSWERS, OUT, SAMPLES, open_page, run_file, score, serve


def main():
    want = [a for a in sys.argv[1:] if not a.startswith("--")]
    engine = "tess" if "--engine" in sys.argv and sys.argv[sys.argv.index("--engine") + 1] == "tess" else "paddle"
    want = [w for w in want if w != "tess"]
    files = sorted(f for f, a in ANSWERS.items() if a.get("scanned") and (not want or any(w in f for w in want)))
    srv, port = serve()
    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        ctx = b.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})
        for f in files:
            page = open_page(ctx, port, keys=[], extra=f"&ocr={engine}" + ("&debug=1" if "--debug" in sys.argv else ""))
            page.on("console", lambda m: print("  [console]", m.text) if m.type in ("error", "warning") else None)
            res, path = run_file(page, SAMPLES / f, timeout=600_000)
            ocr = page.evaluate("window.__pabiao.ocr")
            sc = score(path, ANSWERS[f]) if path else None
            if "--debug" in sys.argv:
                (OUT / (f + ".ocr.json")).write_text(json.dumps(ocr, ensure_ascii=False, indent=0), encoding="utf-8")
                import base64
                for k, url in enumerate(page.evaluate("window.__pabiao.ocrImgs || []")):
                    (OUT / f"{f}.p{k + 1}.png").write_bytes(base64.b64decode(url.split(",", 1)[1]))
            print(f"== {f}  {res['seconds']}s  主线程最长卡 {res['max_main_thread_gap_ms']}ms  {res['title']} | {res.get('line2', '')}")
            for o in ocr or []:
                print("   ocr", {k: v for k, v in o.items() if k != "debug"})
            if res.get("err_text"):
                print("   err", res["err_text"])
            if sc:
                print("   格", sc["cells"], "表", f"{sc['tables_got']}/{sc['tables_expected']}", "错", sc["wrong_flagged"], "标色共", sc["flags_total"])
                for t in sc["tables"]:
                    print("   ", t.get("rows_got"), "/", t["rows_expected"], "行", t.get("cols_got"), "/", t.get("cols_expected"), "列")
                    for w in t["wrong"]:
                        print("     ", w)
            rows.append((f, res, sc))
            page.close()
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
