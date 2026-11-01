"""截图拼图：每份文件一张，行 = 各家，列 = 刚打开 / 干活中 / 出结果。存 bench/截图/<文件名>.png"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "out" / "shots"
DST = ROOT / "截图"
WHO = [("渡表僧", "渡表僧"), ("nanonets", "Nanonets"), ("ilovepdf", "iLovePDF（替补）"), ("pdf24", "PDF24（替补）")]
STEPS = [("1打开", "刚打开"), ("2干活", "干活中"), ("3结果", "出结果")]
W, H, PAD, TOP, LEFT = 560, 376, 12, 44, 220
FONT = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 22)


def main():
    DST.mkdir(exist_ok=True)
    stems = sorted({p.name.split("__")[0] for p in SHOTS.glob("*__*.png")})
    for stem in stems:
        g = Image.new("RGB", (LEFT + 3 * (W + PAD), TOP + len(WHO) * (H + PAD)), "white")
        d = ImageDraw.Draw(g)
        for c, (_, label) in enumerate(STEPS):
            d.text((LEFT + c * (W + PAD) + 8, 8), label, fill="#1d1d1f", font=FONT)
        for r, (key, label) in enumerate(WHO):
            y = TOP + r * (H + PAD)
            d.text((10, y + H // 2 - 14), label, fill="#1d1d1f", font=FONT)
            for c, (suf, _) in enumerate(STEPS):
                x = LEFT + c * (W + PAD)
                p = SHOTS / f"{stem}__{key}_{suf}.png"
                if not p.exists():
                    p2 = SHOTS / f"{stem}__{key}_失败.png"
                    p = p2 if (c == 2 and p2.exists()) else None
                if p:
                    im = Image.open(p).convert("RGB")
                    im.thumbnail((W, H))
                    g.paste(im, (x, y))
                else:
                    d.rectangle((x, y, x + W, y + H), fill="#f5f5f7")
                    d.text((x + 16, y + 16), "没拍到", fill="#86868b", font=FONT)
        g.save(DST / f"{stem}.png", optimize=True)
        print(DST / f"{stem}.png")


if __name__ == "__main__":
    main()
