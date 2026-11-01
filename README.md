# 渡表僧 · 表丢来，你去玩，贫僧超度

原名扒表僧，2026-11-01 Song 改名渡表僧。网址、仓库名还是 pabiao。

PDF 丢进来，Excel 自己下载。扫描件也认得。千手院（QIANSHOU LAB）罗汉一尊。

**网址：https://qianshoulab.github.io/pabiao/**

- 电脑、手机都能用，不用装。选完文件就不用再点了，Excel 自己下载。
- 有字的 PDF（电脑导出的）：在你浏览器里拆，不上传，不用 AI，数字原样搬。表跨页了自动接上，每页重印的表头只留一份，合并表头照原样合并。
- 扫描件、拍照的：
  - **没钥匙**：在浏览器里本地认字（PP-OCRv5），中文、英文、中英混排都认，不上传，不停下来要钥匙。拍歪的、斜着拍的（透视）会先扳正。第一次要下约 25 MB 的模型，存在浏览器里，以后不再下。
  - **有钥匙**：借谷歌 Gemini 的眼睛，每页认两遍对答案，对不上认第三遍，还对不上的格子标红。钥匙出岔子（无效、额度用完、断网）自动改成本地认。要一把免费钥匙（[怎么领](https://qianshoulab.github.io/luruseng/key.html)），钥匙只存在你自己的浏览器里。
- Excel 里的数字是真数字，能求和；`0` 开头的编号保住开头的 `0`；千分位、括号负数、百分号、日期照 PDF 上的样子显示。
- 拿不准的格子标颜色，鼠标放上去看原因：黄 = 拿不准（本地认的把握低、像数字又不像、漏认），橙 = 数字列里认成了字母、按数字改回来的（O→0、l→1、S→5、B→8 这类），红 = 几遍认得不一样。最后一张「扒表记录」列出每张表在第几页、扫描页是谁认的。

## 文件

| 位置 | 是什么 |
|---|---|
| `index.html` | 整个网页，单文件。pdf.js 6.4.299、ExcelJS 4.4.0、onnxruntime-web 1.31.1 从 cdn.jsdelivr.net 引，版本钉死。本地认字的代码在 `#ocr-src` 那段，跑在 Worker 里 |
| `models/` | 本地认字的模型（PP-OCRv5 mobile，Apache-2.0），来源和校验值见 `models/README.md` |
| `samples/` | 自造的样本 PDF 和标准答案（`answers.json` 有字的、`scan_answers.json` 扫描件），内容全是编的 |
| `tests/make_samples.py` | 造有字的样本和 s6 |
| `tests/make_scans.py` | 造扫描件样本：英文 / 中文 / 中英混排 × 300 DPI / 150 DPI 糊的 / 仿手机拍照 |
| `tests/run_e2e.py` | 本机起服务（网页 + 假谷歌），用 Edge 跑全部样本，逐格对答案；扫描件另报「认错的数字里标了颜色的、没标的」、电脑宽和手机宽的用时、第一次下载量 |
| `tests/dev_ocr.py` | 调本地认字用：只跑扫描件，打印每个错格；`--engine tess` 换成 Tesseract.js 对比，`--debug` 存下收拾过的图和框 |
| `tests/check_live.py` | 上线后自检：打开线上网址，丢样本进去对答案（含一份扫描件） |
| `docs/设计记录.md` | 为什么这么做 |
| `bench/比武报告.md` | 跟 Nanonets、iLovePDF、PDF24 拿 9 份公开真文件对打的结果（施工单 011） |

跑测试：

```
python -m venv .venv
.venv\Scripts\pip install playwright openpyxl reportlab pypdfium2 Pillow
.venv\Scripts\python tests\make_samples.py
.venv\Scripts\python tests\make_scans.py
.venv\Scripts\python tests\run_e2e.py
```

制作人：千手院方丈释手 · [千手院总舵](https://qianshoulab.github.io/) · oilsongchengmin@gmail.com
