"""先看一眼对手的网页长啥样：probe.py 网址 名字  → 截图 bench/out/probe_名字.png，打印按钮和上传框"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

url, name = sys.argv[1], sys.argv[2]
out = Path(__file__).resolve().parents[1] / "out"
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_context(viewport={"width": 1280, "height": 860}).new_page()
    pg.goto(url, wait_until="domcontentloaded", timeout=60_000)
    pg.wait_for_timeout(6000)
    print("标题", pg.title(), "|", pg.url)
    pg.screenshot(path=str(out / f"probe_{name}.png"))
    print("上传框", pg.evaluate("[...document.querySelectorAll('input[type=file]')].map(i=>i.outerHTML.slice(0,160))"))
    print("按钮", pg.evaluate("[...document.querySelectorAll('button,[role=button],a.btn')].filter(e=>e.offsetParent).map(e=>e.innerText.trim().slice(0,40)).filter(Boolean).slice(0,40)"))
    b.close()
