"""摸对手的流程：explore.py 网址 名字 上传框选择器 文件 [秒数]
传文件后每 10 秒截一张图、打印看得见的按钮，有下载就存下来。只许传 bench/files/ 里的公开文件。"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

url, name, sel, f = sys.argv[1:5]
secs = int(sys.argv[5]) if len(sys.argv) > 5 else 90
root = Path(__file__).resolve().parents[1]
f = Path(f).resolve()
assert f.parent == (root / "files").resolve(), "只许传 bench/files/ 里的公开文件"
out = root / "out" / "explore"
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    ctx = b.new_context(accept_downloads=True, viewport={"width": 1280, "height": 860})
    pg = ctx.new_page()
    pg.on("download", lambda d: (d.save_as(str(out / f"{name}_{d.suggested_filename}")), print("下载", d.suggested_filename, flush=True)))
    pg.goto(url, wait_until="domcontentloaded", timeout=60_000)
    pg.wait_for_timeout(4000)
    t0 = time.time()
    pg.set_input_files(sel, str(f))
    k = 0
    while time.time() - t0 < secs:
        pg.wait_for_timeout(10_000)
        k += 1
        pg.screenshot(path=str(out / f"{name}_{k:02d}.png"))
        btn = pg.evaluate("[...document.querySelectorAll('button,[role=button],a')].filter(e=>e.offsetParent).map(e=>e.innerText.trim().slice(0,30)).filter(Boolean)")
        print(f"{int(time.time() - t0)}s", pg.url[:80], btn[:25], flush=True)
    b.close()
