"""精加工每轮重比：本机起服务跑改过的 index.html（不贴钥匙 = 本地认字），同一批比武文件、同一个评分器。
用法：rerun.py 轮名 [文件名关键字…] [--once] [--show]
  --once 每份只跑一遍（调代码时用）；默认三遍取中位数
  --show 打印每张表的前几行
结果写 bench/out/<轮名>.json，Excel 存 bench/out/<轮名>/
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "tests"))
sys.path.insert(0, str(Path(__file__).parent))
from playwright.sync_api import sync_playwright  # noqa: E402

import score as SC  # noqa: E402
from run_e2e import open_page, serve  # noqa: E402


def main():
    name = sys.argv[1]
    want = [a for a in sys.argv[2:] if not a.startswith("--")]
    runs = 1 if "--once" in sys.argv else 3
    out = ROOT / "out" / name
    out.mkdir(parents=True, exist_ok=True)
    res_path = ROOT / "out" / f"{name}.json"
    report = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else {}
    srv, port = serve()
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge")
        for f in SC.ANSWERS:
            if want and not any(w in f for w in want):
                continue
            secs = []
            for k in range(runs):
                ctx = b.new_context(accept_downloads=True, viewport={"width": 1280, "height": 900})
                page = open_page(ctx, port, keys=[], extra="&api=http://127.0.0.1:9/v1beta")
                t0 = time.time()
                with page.expect_download(timeout=900_000) as d:
                    page.set_input_files("#pick", str(ROOT / "files" / f))
                secs.append(round(time.time() - t0, 1))
                path = out / (Path(f).stem + ".xlsx")
                d.value.save_as(str(path))
                page.wait_for_function("window.__pabiao.phase === 'done'", timeout=60_000)
                ctx.close()
            sc = SC.score(path, f)
            report[f] = {"seconds": secs, "median": statistics.median(secs), "score": sc}
            print(f"{f}  准 {sc['body']}  表头 {sc['header']}  标色错 {sc['wrong_flagged']}  悄悄错 {sc['wrong_silent']}  {secs}", flush=True)
            if "--show" in sys.argv:
                for t in sc["tables"]:
                    print("   ", t["blocks"], t["wrong"][:6])
                for n, g, _ in SC.load(path):
                    print("   ", n, len(g), "行")
                    for r in g[:6]:
                        print("      ", [str(c)[:28] if c is not None else None for c in r][:9])
            res_path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        b.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
