# PaperFlow

**论文排版检查与优化**

Academic Layout Review & Refinement

PaperFlow 是面向论文与长文档的 agent skill。检查图文位置、页面布局和可读性；结合源文件修复，并重新渲染确认效果。

## 它会检查什么

| 范围 | 重点 |
|---|---|
| 图表与正文 | 图表是否靠近关键解释段，首次提及与主要讨论是否对应，双栏读序是否顺畅 |
| 页面布局 | 裁切、重叠、留白、分页、浮动体堆积、孤行和孤标题 |
| 字体与图表 | 最终尺寸下的字号、轴标、图例、多面板、表格续页与单位 |
| 公式、图注与引用 | 公式折行、编号、图注位置、交叉引用及脚注 |
| 无障碍与交付 | 文字层、阅读顺序、色彩之外的区分方式、模板要求 |

PDF 脚本采集坐标、字号和引用等证据，智能体结合渲染页面作出视觉与语义判断，再通过 LaTeX、Word、Typst、HTML 等源文件完成修复。

## 三个关键设计

- **跟着解释找图。** 同时关注首次提及和真正需要看图的段落，避免把图移近导读、却移远核心讨论。
- **理解排版例外。** 遵循投稿模板，保留文末图、合理空白页等安排；距离和字号阈值可配置。
- **改完再看。** 重新构建、检查相邻页，并核对文字、数值、限定和图表内容是否保留。

## 安装

```bash
git clone https://github.com/YuanMing-11/paperflow.git
cd paperflow
python3 scripts/install_skill.py
```

默认安装到 `$CODEX_HOME/skills/paperflow`，未设置时使用 `~/.codex/skills/paperflow`。安装后在新会话中调用 `$paperflow`。

运行 PDF 工具需要 Python 3.10+ 和 PyMuPDF：

```bash
python3 -m pip install -r requirements.txt
```

## 使用

检查论文：

> 用 $paperflow 检查这篇论文，重点看图表与关键解释段的距离、图表可读性和分页。先给问题清单。

修复排版：

> 用 $paperflow 修复这些排版问题，保留全部科学内容和限定，重新编译后验证。

提供最终 PDF 即可开展审查；同时提供源文件，可以进一步修改和重建。

也可以单独运行 PDF 证据收集器，生成 JSON/HTML 报告和页面图像：

```bash
python3 scripts/audit_pdf.py manuscript.pdf --out audit/before --render
```

## 文档

- [检查目录](references/checks.md)：11 类、50 项审查指引
- [图文距离判断](references/proximity.md) · [源文件修复](references/repairs.md)
- [工具与配置](references/tools.md) · [报告格式](references/reporting.md)
- [设计参考](references/source-review.md) · [测试与验证](evaluation/summary.md)
- [版本说明](RELEASE_NOTES.md)

## 许可

原创代码、文档和合成样例采用 [MIT](LICENSE)。PyMuPDF/MuPDF 依赖适用其 [AGPL 或商业许可](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)。
