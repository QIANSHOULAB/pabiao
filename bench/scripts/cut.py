"""截页：cut.py 原件.pdf 页号(从1起，逗号分隔) 输出.pdf
也能把图片包成单页 PDF：cut.py 图.jpg - 输出.pdf [dpi] [裁剪 x0,y0,x1,y1 比例]
用 .venv 里已有的 pypdfium2，不装 pypdf。"""
import sys
from pathlib import Path

import pypdfium2 as pdfium

src, pages, dst = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
if src.suffix.lower() == ".pdf":
    s = pdfium.PdfDocument(str(src))
    out = pdfium.PdfDocument.new()
    out.import_pages(s, [int(p) - 1 for p in pages.split(",")])
    out.save(dst)
    print(dst, len(out), "页")
else:
    from PIL import Image
    dpi = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    im = Image.open(src).convert("RGB")
    if len(sys.argv) > 5:
        c = [float(x) for x in sys.argv[5].split(",")]
        W, H = im.size
        im = im.crop((int(c[0] * W), int(c[1] * H), int(c[2] * W), int(c[3] * H)))
    im.save(dst, "PDF", resolution=dpi)
    print(dst, im.size, f"{dpi}dpi")
