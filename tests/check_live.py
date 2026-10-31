"""上线后自检：用 Edge 打开线上网址，丢样本 1 和样本 4 进去，对答案。

用法：.venv/Scripts/python tests/check_live.py [网址]   默认 https://qianshoulab.github.io/pabiao/
退出码 0 = 全对。
"""
import sys
import urllib.request

from playwright.sync_api import sync_playwright

from run_e2e import ANSWERS, OUT, SAMPLES, score

URL = sys.argv[1] if len(sys.argv) > 1 else "https://qianshoulab.github.io/pabiao/"


def main():
    with urllib.request.urlopen(URL, timeout=30) as r:
        html = r.read().decode("utf-8")
        print("HTTP", r.status, "· 标题在" if "<title>扒表僧" in html else "· 标题不对")
    ok = "<title>扒表僧" in html
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        ctx = b.new_context(accept_downloads=True)
        for f in ["s1_简单表.pdf", "s4_合并表头.pdf"]:
            page = ctx.new_page()
            page.goto(URL)
            page.wait_for_function("window.__pabiao && window.__pabiao.ready", timeout=60_000)
            with page.expect_download(timeout=120_000) as d:
                page.set_input_files("#pick", str(SAMPLES / f))
            OUT.mkdir(parents=True, exist_ok=True)
            path = OUT / ("live_" + f.replace(".pdf", ".xlsx"))
            d.value.save_as(str(path))
            s = score(path, ANSWERS[f])
            good = s["num_wrong"] == 0 and s["text_wrong"] == 0 and s["header_wrong"] == 0 and s["tables_got"] == s["tables_expected"]
            ok = ok and good
            print(f, "全对" if good else "有错", s["cells"])
            page.close()
        b.close()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
