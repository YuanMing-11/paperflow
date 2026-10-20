# 综合排版示例

一篇两页的合成研究短文，集中展示 PaperFlow 的排版优化目标。

[优化前](before.pdf) · [优化后](after.pdf)

- 图表靠近结果解释，图注与图保持成组。
- 标题跟随正文，交叉引用指向正确编号。
- 图例、刻度字号和系列区分更清晰。
- 表头、数值列和行间层次便于扫读。
- 长公式合理分行，编号对齐。

两版沿用相同的示例内容与数据。文档中的研究与观测均为虚构，用于展示排版效果。

## 重新生成

```bash
python3 -m pip install reportlab matplotlib pymupdf
python3 generate.py
python3 render_comparison.py
```
