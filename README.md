# 扒表僧 · 施主丢卷，贫僧扒表

PDF 丢进来，Excel 自己下载。扫描件也认得。千手院（QIANSHOU LAB）罗汉一尊。

**网址：https://qianshoulab.github.io/pabiao/**

- 电脑、手机都能用，不用装。选完文件就不用再点了，Excel 自己下载。
- 有字的 PDF（电脑导出的）：在你浏览器里拆，不上传，不用 AI，数字原样搬。表跨页了自动接上，每页重印的表头只留一份，合并表头照原样合并。
- 扫描件、拍照的：借谷歌 Gemini 的眼睛，每页认两遍对答案，对不上认第三遍，还对不上的格子标红。要一把免费钥匙（[怎么领](https://qianshoulab.github.io/luruseng/key.html)），钥匙只存在你自己的浏览器里。
- Excel 里的数字是真数字，能求和；`0` 开头的编号保住开头的 `0`；千分位、括号负数、百分号、日期照 PDF 上的样子显示。拿不准的格子标黄，鼠标放上去看原因；最后一张「扒表记录」列出每张表在第几页。

## 文件

| 位置 | 是什么 |
|---|---|
| `index.html` | 整个网页，单文件。pdf.js 6.4.299、ExcelJS 4.4.0 从 cdn.jsdelivr.net 引，版本钉死 |
| `samples/` | 自造的样本 PDF 和标准答案 `answers.json`，内容全是编的 |
| `tests/make_samples.py` | 造样本 |
| `tests/run_e2e.py` | 本机起服务（网页 + 假谷歌），用 Edge 跑全部样本，逐格对答案 |
| `docs/设计记录.md` | 为什么这么做 |

跑测试：

```
python -m venv .venv
.venv\Scripts\pip install playwright openpyxl reportlab pypdfium2 Pillow
.venv\Scripts\python tests\make_samples.py
.venv\Scripts\python tests\run_e2e.py
```

制作人：千手院方丈释手 · [千手院总舵](https://qianshoulab.github.io/) · oilsongchengmin@gmail.com
