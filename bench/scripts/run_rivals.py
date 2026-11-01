"""对手跑分：干净的 Edge，每遍新开，不登录。每份跑三遍，秒数 = 选好文件 → 文件下载下来（上传、排队、网速都算在里面）。
第一遍拍三张图：刚打开、干活中、出结果。只传 bench/files/ 里的公开文件。
用法：run_rivals.py 对手名(nanonets/ilovepdf/pdf24) [文件名关键字…]   结果写 bench/out/rivals.json
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
SHOTS = ROOT / "out" / "shots"
RUNS = 3
URLS = {"nanonets": "https://tools.nanonets.com/pdf-to-excel",
        "ilovepdf": "https://www.ilovepdf.com/pdf_to_excel",
        "pdf24": "https://tools.pdf24.org/en/pdf-to-excel"}


def shot(page, path, on):
    if on:
        page.screenshot(path=str(path))


def flow(rival, page, pdf, sp, shots):
    """跑一遍，返回 (download, 备注)。每家的点法跟真人一样：人点哪个按钮，脚本就点哪个。"""
    if rival == "nanonets":
        page.set_input_files("#file", str(pdf))
        page.wait_for_timeout(5000)
        shot(page, sp("2干活"), shots)
        btn = page.get_by_text("Download CSV")
        btn.wait_for(state="visible", timeout=240_000)
        shot(page, sp("3结果"), shots)
        with page.expect_download(timeout=120_000) as d:
            btn.click()
        return d.value, ""
    if rival == "ilovepdf":
        page.set_input_files("input[type=file]", str(pdf))
        go = page.get_by_text("Convert to EXCEL")
        go.wait_for(state="visible", timeout=120_000)
        got = []
        page.once("download", lambda _: got.append(1))
        with page.expect_download(timeout=240_000) as d:
            go.click()
            page.wait_for_timeout(1500)
            shot(page, sp("2干活"), shots)
            # 扫描件：弹窗问要不要 OCR（OCR 是付费功能），免费用户只能点「Continue without OCR」，Excel 里只有一张图
            no_ocr = page.get_by_text("Continue without OCR").locator("visible=true").first
            note = "下载页自动开始下载"
            for _ in range(240):                     # 下载先到就不等；弹窗先到就点
                if got:
                    break
                if no_ocr.is_visible():
                    note = "扫描件弹窗要 OCR（付费），点了 Continue without OCR"
                    no_ocr.click()
                    break
                page.wait_for_timeout(250)
        page.wait_for_timeout(1500)
        shot(page, sp("3结果"), shots)
        return d.value, note
    if rival == "pdf24":
        page.set_input_files("input[type=file]", str(pdf))
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="Convert").click()
        page.wait_for_timeout(1500)
        shot(page, sp("2干活"), shots)
        mon = page.frame_locator("iframe[src*='job-monitor']")      # 结果框在一个 iframe 里
        mon.get_by_text("has converted your PDF").first.wait_for(state="visible", timeout=240_000)
        dl = mon.get_by_text("Download", exact=True).first
        shot(page, sp("3结果"), shots)
        with page.expect_download(timeout=120_000) as d:
            dl.click()
        return d.value, ""
    raise ValueError(rival)


def one(browser, rival, pdf, shots):
    ctx = browser.new_context(accept_downloads=True, viewport={"width": 1280, "height": 860})
    page = ctx.new_page()
    page.goto(URLS[rival], wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(4000)
    sp = lambda s: SHOTS / f"{pdf.stem}__{rival}_{s}.png"
    shot(page, sp("1打开"), shots)
    t0 = time.time()
    try:
        d, note = flow(rival, page, pdf, sp, shots)
        secs = time.time() - t0
        ext = Path(d.suggested_filename).suffix or ".bin"
        path = ROOT / "out" / rival / (pdf.stem + ext)
        path.parent.mkdir(parents=True, exist_ok=True)
        d.save_as(str(path))
        ctx.close()
        return secs, path, note
    except Exception as e:
        page.screenshot(path=str(SHOTS / f"{pdf.stem}__{rival}_失败.png"))
        ctx.close()
        return None, None, f"失败：{type(e).__name__}: {str(e)[:200]}"


def main():
    rival, want = sys.argv[1], sys.argv[2:]
    SHOTS.mkdir(parents=True, exist_ok=True)
    res_path = ROOT / "out" / "rivals.json"
    report = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    report.setdefault(rival, {})
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        for name in SC.ANSWERS:
            if want and not any(w in name for w in want):
                continue
            pdf = ROOT / "files" / name
            secs, path, notes = [], None, []
            for k in range(RUNS):
                s, pth, note = one(browser, rival, pdf, shots=(k == 0))
                notes.append(note)
                print(rival, name, f"第{k + 1}遍", None if s is None else round(s, 1), note, flush=True)
                if s is None:
                    break
                secs.append(round(s, 1))
                path = pth
            r = {"seconds": secs, "median": statistics.median(secs) if secs else None, "notes": notes}
            if path:
                r["format"] = path.suffix
                r["score"] = SC.score(path, name)
                print(rival, name, "准", r["score"]["body"], "表头", r["score"]["header"], flush=True)
            report[rival][name] = r
            res_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
