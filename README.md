# PaperFlow

**论文排版检查与优化**

Academic Layout Review & Refinement

An evidence-based agent skill for academic document layout: figure–text proximity, reading flow, typography, tables, equations, captions, accessibility, and verified source repairs.

面向论文与长文档的排版审查和修复 skill：先看最终页面，再结合源文件修复，并验证内容保留。

v0.1.0 · Python 3.10+ · PDF 自动取证 + 智能体视觉/语义审查

## 能做什么

[检查目录](references/checks.md)包含 **11 类、50 项**审查任务。它们是 skill 的工作覆盖面，**不是 50 项已经全自动实现的检测器**。

| 范围 | 内容 |
|---|---|
| 图文导航 | 首次提及、关键解释段与图表距离；双栏读序；图号和子图对应 |
| 页面布局 | 裁切、重叠、留白、浮动体堆积、孤行孤标题、分页和栏平衡 |
| 字体与图表 | 最终尺寸下的字号、轴标、图例、多面板、表格续页与单位 |
| 公式、图注、引用 | 公式折行与编号、图注黏连、失效引用、文献及脚注 |
| 无障碍与交付 | 色彩之外的编码、文字层、替代描述、阅读顺序和模板要求 |
| 修改后复查 | 全文和数值保留、图表系列、相邻页、其他引用及重新分页 |

采用三层能力：

1. **脚本取证**：实际 PDF 坐标、字号、图注/引用候选、页差、页面占用、TeX 日志和版本差异，生成 JSON/HTML。
2. **智能体判断**：看渲染页、读对应段落、核对编号作用域、决定例外及修复优先级。
3. **源文件修复**：通过现有构建工具修改和导出 LaTeX、Word、Typst、HTML 或其他生成式文档，再复查。

只有 PDF 时可以完整开展视觉审查，但无法验证未提供的源数据或直接保证源文件修复。没有编译器时，源文件建议与最终版式验证会明确分开。

## 设计方法

- 从视觉审查工作流吸收：编译 → 看成品 → 局部修改 → 重编译 → 检查相邻页。
- 从图表工具吸收：最终放置尺寸、结构化几何证据、多面板一致性。
- 从模板工作吸收：先找浮动队列原因，阈值可配置，允许合理例外。
- 在图文距离上同时保留**所有提及**和**需要看图的解释段**，不只优化第一次出现图号的位置。
- 报告区分实测、启发式、视觉判断与未检查；保留必要限定、数值、单位、图例和数据系列。

核查了 5 个 2026 年公开项目、一篇 2026 年图文关联研究，并参考 2025 年官方投稿规范。方法吸收、固定提交、许可证及不应照搬的规则见[案例研究](references/source-review.md)。这些基础检查并非本项目首创。

## 安装与使用

克隆此仓库并安装：

```bash
git clone https://github.com/YuanMing-11/paperflow.git
cd paperflow
python3 scripts/install_skill.py
```

默认安装到 `$CODEX_HOME/skills/paperflow`，未设置 `CODEX_HOME` 时使用 `~/.codex/skills/paperflow`。已有安装会保留并报错。可用 `--skills-dir /path/to/skills` 指定其他技能目录。安装器只复制 skill，不修改 Python 环境；若当前会话已缓存技能列表，在新会话使用。

依赖缺失时，可创建隔离环境：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
source .venv/bin/activate
```

对智能体说：

> 用 $paperflow 检查这篇论文，重点看图表与关键解释段的距离、图表可读性和分页。先给问题清单。

或者：

> 用 $paperflow 直接修复这些排版问题，保留全部科学内容和限定，重新编译后验证。

单独运行证据收集器：

```bash
python3 scripts/audit_pdf.py manuscript.pdf --out audit/before --render
python3 scripts/audit_build_log.py main.log --out audit/build-log.json
python3 scripts/compare_reports.py audit/before/report.json audit/after/report.json --out audit/comparison.json
```

如果投稿要求图表后置：

```bash
python3 scripts/audit_pdf.py manuscript.pdf --out audit/before \
  --profile profiles/end-matter.json --render
```

具体配置和输出字段见[工具说明](references/tools.md)。`exit 0` 只表示运行完成；自动结果始终需要审查。脚本在本地处理，不主动上传文档。

## 已做的验证

- **10 份独立设计 PDF / 23 页**：136 项自动不变量通过，包括目录过滤、近/远引用、图表后置例外、矢量图、双栏、补充材料和扫描页。
- **9 项代码回归测试**通过；修复了图注中引用其他图、补充表格分类、子图不匹配和硬链接覆盖输入问题。
- **独立智能体审查 3 份样例**：正确保留后置图、区分导读与关键解释，并明确扫描页的文本检查不可用。
- **独立修复任务**：将一个原始 3 页合成报告调整为 1 页，图文相邻；全文、字号和图中矢量保持一致，7 项内容保留检查通过。
- **真实论文测试**：对 2026 年一篇 40 页论文完成提取和渲染，抽查问题页；据此修复图注续行误识别，并记录示例论文编号、脚注粘连等限制。

这是小规模行为验证，尚未建立真实论文上的准确率、全面召回率或读者收益。LaTeX/Word/Typst 的修复指导已提供；本次实际修复验证使用 Python/ReportLab 源文件，未把它说成所有构建链都已测试。

复现测试：

```bash
python3 -m pip install -r tests/requirements.txt
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/make_fixtures.py --out tests/generated
python3 tests/evaluate.py --fixtures tests/generated
```

测试运行器只给可观测的自动不变量评分；语义与视觉行为需要独立看图评审。详见[验证记录](evaluation/summary.md)。

项目最初以 `paper-layout-audit` 为内部名称完成验证。原始评估记录及哈希保持不变；发布版统一命名为 PaperFlow，安装和调用名称为 `paperflow`。更名后的重新验证见[发布说明](RELEASE_NOTES.md)。

## 已知边界

无内置 OCR；表格语义、重叠、公式折行、屏幕阅读距离和正式无障碍合规主要依赖视觉/结构审查。正文与嵌入示例的图号可能同名；脚注上标可能粘成图号；图片中的字号和数据完整性不能由文本提取建立。缺少原始数据时，不宣称所有曲线/观测都完整。

两页距离、7 pt 字号和稀疏页比例均是可调筛查值，不能当作期刊标准。没有内置未经核对的“全期刊合规”规则库。

## 许可

本仓库原创代码、文档和合成样例采用 [MIT](LICENSE)。研究案例独立概括，没有复制第三方实现。依赖保留各自许可证；PyMuPDF/MuPDF 提供 AGPL 与商业许可，见[官方说明](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)。本包不捆绑第三方库或真实论文全文。
