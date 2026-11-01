"""把图片或 PDF 的某页缩成看得清的小图：thumb.py 输入 输出.png [页号(从1起)] [宽] [裁剪 x0,y0,x1,y1 比例]"""
import sys
from pathlib import Path
from PIL import Image
src, dst = Path(sys.argv[1]), sys.argv[2]
page = int(sys.argv[3]) if len(sys.argv) > 3 else 1
width = int(sys.argv[4]) if len(sys.argv) > 4 else 1400
crop = [float(x) for x in sys.argv[5].split(",")] if len(sys.argv) > 5 else None
if src.suffix.lower() == ".pdf":
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(src))
    pg = pdf[page - 1]
    im = pg.render(scale=4 if crop else 2).to_pil()
else:
    im = Image.open(src)
im = im.convert("RGB")
if crop:
    W, H = im.size
    im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
if im.width > width:
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
im.save(dst)
print(im.size)
