"""上线后自检：用 Edge 打开线上网址，丢样本进去对答案。

有字的 s1、s4 必须全对；扫描件 s6、o4（没钥匙，本地认）要出表，并且认错的数字全都标了颜色。
用法：.venv/Scripts/python tests/check_live.py [网址]   默认 https://qianshoulab.github.io/pabiao/
退出码 0 = 过线。
"""
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

from run_e2e import ANSWERS, OUT, SAMPLES, score

URL = sys.argv[1] if len(sys.argv) > 1 else "https://qianshoulab.github.io/pabiao/"


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        html = r.read().decode("utf-8")
        print("HTTP", r.status, "· 标题在" if "<title>扒表僧" in html else "· 标题不对")
    ok = "<title>扒表僧" in html
    for m in ("models/ppocrv5_mobile_det.onnx", "models/ppocrv5_mobile_rec.onnx", "models/ppocrv5_dict.txt"):
        req = urllib.request.Request(URL.rstrip("/") + "/" + m, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            print(m, r.status, r.headers.get("Content-Length"))
            ok = ok and r.status == 200
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        ctx = b.new_context(accept_downloads=True)
        for f in ["s1_简单表.pdf", "s4_合并表头.pdf", "s6_扫描版.pdf", "o4_中文表_300dpi.pdf"]:
            page = ctx.new_page()
            page.goto(URL)
            page.wait_for_function("window.__pabiao && window.__pabiao.ready", timeout=60_000)
            t0 = time.time()
            with page.expect_download(timeout=600_000) as d:
                page.set_input_files("#pick", str(SAMPLES / f))
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / ("live_" + f.replace(".pdf", ".xlsx"))
            d.value.save_as(str(path))
            s = score(path, ANSWERS[f])
            if ANSWERS[f].get("scanned"):
                good = s["tables_got"] == s["tables_expected"] and s["wrong_flagged"]["num_silent"] == 0
            else:
                good = s["num_wrong"] == 0 and s["text_wrong"] == 0 and s["header_wrong"] == 0 and s["tables_got"] == s["tables_expected"]
            ok = ok and good
            print(f, "过" if good else "没过", f"{time.time() - t0:.1f}s", s["cells"], s["wrong_flagged"])
            page.close()
        b.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
