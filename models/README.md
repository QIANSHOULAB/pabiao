# 本地认字用的模型

扫描件没钥匙时，渡表僧在浏览器里认字，用的是百度飞桨 PaddleOCR 的 PP-OCRv5 mobile。许可证 Apache-2.0，全文见同目录 `LICENSE`。这里的文件没有改过权重。

| 文件 | 来源 | 大小 | SHA-256 |
|---|---|---|---|
| `ppocrv5_mobile_det.onnx` | [PaddlePaddle/PP-OCRv5_mobile_det_onnx](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det_onnx) `inference.onnx`，提交 `e6f4fa85f00e168c862bc462aebca69eef9b3d3d` | 4,826,518 | `a431985659dc921974177a95adcfbb90fd9e51989a5e04d70d0b75f597b6e61d` |
| `ppocrv5_mobile_rec.onnx` | [PaddlePaddle/PP-OCRv5_mobile_rec_onnx](https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_rec_onnx) `inference.onnx`，提交 `ed152b8b495f84de93cda5709d768548a9127622` | 16,534,782 | `da72dc72ca4dc220df0dfde68c1dedc31c58d3e76a25871122e5056227d50092` |
| `ppocrv5_dict.txt` | 同上 rec 仓库 `inference.yml` 里的 `character_dict`，一行一个，共 18,383 个 | 74,012 | `d1979e9f794c464c0d2e0b70a7fe14dd978e9dc644c0e71f14158cdf8342af1b` |

- 模型输出 18,385 类：0 是空白，1–18,383 对应字典，最后一类是空格。
- 网页第一次认扫描件时下载这几个文件，存进浏览器的 Cache Storage（名字 `pabiao-ocr-1`），以后不再下。换模型时连文件名一起换，免得浏览器拿旧的。
- 推理用 onnxruntime-web 1.31.1（MIT），从 cdn.jsdelivr.net 引。
