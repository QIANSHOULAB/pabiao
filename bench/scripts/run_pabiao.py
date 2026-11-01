"""渡表僧跑分：线上网址，干净的 Edge（每遍新开，不贴钥匙 = 本地认字），每份跑三遍。
秒数 = 选好文件 → Excel 下载下来。第一遍拍三张图：刚打开、干活中、出结果。
用法：run_pabiao.py [文件名关键字…]   结果写 bench/out/pabiao.json，Excel 存 bench/out/pabiao/
"""
import json
import statistics
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).parent))
import score as SC  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
URL = "https://qianshoulab.github.io/pabiao/"
OUT = ROOT / "out" / "pabiao"
SHOTS = ROOT / "out" / "shots"
RUNS = 3


def one(browser, pdf, shots):
    ctx = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 860})
    page = ctx.new_page()
    page.goto(URL)
    page.wait_for_function("window.__pabiao && document.querySelector('#drop')")
    page.wait_for_load_state("networkidle")
    if shots:
        page.screenshot(path=str(SHOTS / f"{pdf.stem}__渡表僧_1打开.png"))
    t0 = time.time()
    with page.expect_download(timeout=900_000) as d:
        page.set_input_files("#pick", str(pdf))
        if shots:
            try:
                page.wait_for_function("window.__pabiao.phase === 'work'", timeout=10_000)
                page.wait_for_timeout(1500)
                page.screenshot(path=str(SHOTS / f"{pdf.stem}__渡表僧_2干活.png"))
            except Exception:
                pass
    secs = time.time() - t0
    dl = d.value
    page.wait_for_function("window.__pabiao.phase === 'done'", timeout=60_000)
    page.wait_for_timeout(500)
    if shots:
        page.screenshot(path=str(SHOTS / f"{pdf.stem}__渡表僧_3结果.png"))
    path = OUT / (pdf.stem + ".xlsx")
    dl.save_as(str(path))
    log = page.evaluate("window.__pabiao.log.slice(-6)")
    ctx.close()
    return secs, path, log


def main():
    want = sys.argv[1:]
    OUT.mkdir(parents=True, exist_ok=True)
    SHOTS.mkdir(parents=True, exist_ok=True)
    res_path = ROOT / "out" / "pabiao.json"
    report = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for name in SC.ANSWERS:
            if want and not any(w in name for w in want):
                continue
            pdf = ROOT / "files" / name
            secs, logs = [], None
            for k in range(RUNS):
                s, path, logs = one(browser, pdf, shots=(k == 0))
                secs.append(round(s, 1))
                print(name, f"第{k + 1}遍", secs[-1], "秒", flush=True)
            sc = SC.score(path, name)
            report[name] = {"seconds": secs, "median": statistics.median(secs), "score": sc, "log": logs}
            print(name, "准", sc["body"], "表头", sc["header"], "错了标色", sc["wrong_flagged"], "悄悄错", sc["wrong_silent"], flush=True)
            res_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
