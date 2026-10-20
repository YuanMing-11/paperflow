# 2025–2026 学术排版审查案例核验

2025–2026公开案例；最终入选项全部在2026年。优秀指可核验且能贡献独立实践，不表示已通过本次效果benchmark。

官方GitHub REST API仓库、提交、目录树与文件内容；官方GitHub网页；arXiv作者论文。固定revision，独立总结，未复制实现。

GitHub最早默认分支commit是当前公开历史的可见起点，不等同于创作起始日；copyright年份不能当发布日期。latest不是pushed_at。

| 案例 | 可见最早提交/发表 | 最近提交 | 许可 |
|---|---|---|---|
| andrehuang/academic-writing-agents | 2026-03-26 | 2026-03-28 | MIT |
| licongxu/cosmo-agent-skills | 2026-05-18 | 2026-06-18 | MIT |
| enesgul23/scientific-figure-skills | 2026-05-19 | 2026-09-03 | MIT |
| xwysyy-studio/Paper-Typoster | 2026-06-04 | 2026-06-04 | MIT |
| huozuilv/Elsevier-LaTeX-Floats | 2026-06-19 | 2026-06-19 | 未声明 |
| Connecting the Dots: Surfacing Structure in Documents through AI-Generated Cross-Modal Links | 2026-02-18 | — | CC-BY-4.0 |

## latex-layout-auditor

固定版本：`d4d9d3a21afbccd4aee9237a70611429e7df4fba`。
- [agents/latex-layout-auditor.md](https://github.com/andrehuang/academic-writing-agents/blob/d4d9d3a21afbccd4aee9237a70611429e7df4fba/agents/latex-layout-auditor.md)
- [LICENSE](https://github.com/andrehuang/academic-writing-agents/blob/d4d9d3a21afbccd4aee9237a70611429e7df4fba/LICENSE)；Copyright (c) 2025 Haiwen Huang。若复用代码/原文，保留MIT版权与许可。

可吸收：
- 按浮动体label及页码建立问题清单，连结渲染症状与源文件建议。
- 覆盖子图、图注、尺寸、引用顺序和距首次引用的位置。

不能盲用：
- 独立浮动页未必浪费；双栏长图、期刊要求和阅读任务可能需要整页。
- 不能只认cref，合法引用还可能来自ref、autoref、Typst引用或正文编号。
- 不能因使用[b]就判对齐错误，需检查输出。

证据范围：文字agent规范；未提供距离测量脚本或该审查器准确率数据。

## cosmo-layout-and-figure-review

固定版本：`6174ecc6accf59abb9ab5d4e8d06824667a753fb`。
- [skills/paper-writing/paper-layout-review/SKILL.md](https://github.com/licongxu/cosmo-agent-skills/blob/6174ecc6accf59abb9ab5d4e8d06824667a753fb/skills/paper-writing/paper-layout-review/SKILL.md)
- [skills/plotting/vlm-figure-audit/SKILL.md](https://github.com/licongxu/cosmo-agent-skills/blob/6174ecc6accf59abb9ab5d4e8d06824667a753fb/skills/plotting/vlm-figure-audit/SKILL.md)
- [LICENSE](https://github.com/licongxu/cosmo-agent-skills/blob/6174ecc6accf59abb9ab5d4e8d06824667a753fb/LICENSE)；Copyright (c) 2026 Licong Xu。若复用代码/原文，保留MIT版权与许可。

可吸收：
- 源文件编译→看成品→记录问题→最小修改→重编译，检查原问题页及相邻页，最后全篇扫描。
- 图表用最终印刷宽度检查；核对图例、面板、单位与图注。
- 曲线和散点不能只看好不好看：核查每个图例系列、完整范围、异常缺段；有数据时交叉核查。

不能盲用：
- 三分之一栏留白只能作可调启发式，不能单凭空白推断浮动队列阻塞。
- [H]/placeins不能成为“离首次引用远”的通用理由。
- 减少小数位、缩短正文、挪到附录涉及内容，应明确单独审查。
- 零WARN才合格容易无限优化；应允许有理由接受的例外并明确未检查项。

证据范围：两个互补文字skill，依赖视觉判断；并非确定性PDF质量检测器。

## scientific-figure-suite

固定版本：`df72094211b860580e25275b2cc668a0aba0b9d9`。
- [codex/skills/scientific-figure-suite/scripts/audit_multipanel_layout.py](https://github.com/enesgul23/scientific-figure-skills/blob/df72094211b860580e25275b2cc668a0aba0b9d9/codex/skills/scientific-figure-suite/scripts/audit_multipanel_layout.py)
- [codex/skills/scientific-figure-suite/scripts/audit_text_layout.py](https://github.com/enesgul23/scientific-figure-skills/blob/df72094211b860580e25275b2cc668a0aba0b9d9/codex/skills/scientific-figure-suite/scripts/audit_text_layout.py)
- [codex/skills/scientific-figure-suite/scripts/audit_render_quality.py](https://github.com/enesgul23/scientific-figure-skills/blob/df72094211b860580e25275b2cc668a0aba0b9d9/codex/skills/scientific-figure-suite/scripts/audit_render_quality.py)
- [codex/skills/scientific-figure-suite/scripts/audit_accessibility.py](https://github.com/enesgul23/scientific-figure-skills/blob/df72094211b860580e25275b2cc668a0aba0b9d9/codex/skills/scientific-figure-suite/scripts/audit_accessibility.py)
- [LICENSE](https://github.com/enesgul23/scientific-figure-skills/blob/df72094211b860580e25275b2cc668a0aba0b9d9/LICENSE)；Copyright (c) 2026 Scientific Figure Skills Claude contributors。若复用代码/原文，保留MIT版权与许可。

可吸收：
- 将面板bbox、文字bbox、字号、色彩语义、渲染文件及基线拆成可检查的结构化证据。
- 检查面板边界/重叠、同一语义跨面板颜色一致；保存hash及报告用于追溯。

不能盲用：
- 许多检查读取提供的JSON：colorblind_safe=true或overlap_checked=true是声明，不是视觉证明。
- render_quality实际检查尺寸、像素方差、SVG文字标记和hash；hash变化不等于视觉退化。
- 统一6pt、最多12个直接标签、色条必须手工fallback等是配置选择，不宜推广为所有出版物硬规则。

证据范围：已阅读四个实际Python审查脚本；未执行其套件，也未独立验证脚本准确率。

## paper-typoster

固定版本：`c35fa9aa82717add68c1365100fdb03f2dd2c0a2`。
- [src/poster.typ](https://github.com/xwysyy-studio/Paper-Typoster/blob/c35fa9aa82717add68c1365100fdb03f2dd2c0a2/src/poster.typ)
- [tools/poster-check.py](https://github.com/xwysyy-studio/Paper-Typoster/blob/c35fa9aa82717add68c1365100fdb03f2dd2c0a2/tools/poster-check.py)
- [tools/poster-rules.toml](https://github.com/xwysyy-studio/Paper-Typoster/blob/c35fa9aa82717add68c1365100fdb03f2dd2c0a2/tools/poster-rules.toml)
- [LICENSE](https://github.com/xwysyy-studio/Paper-Typoster/blob/c35fa9aa82717add68c1365100fdb03f2dd2c0a2/LICENSE)；Copyright (c) 2026 xwysyy。若复用代码/原文，保留MIT版权与许可。

可吸收：
- 通过Typst measure取得真实布局高度，保持章节顺序的动态规划分栏。
- 导出自然高度、渲染高度、栏间差和字体基准；checker比较两种高度识别内容压缩。
- 把视觉平衡阈值放入配置，并将缺少PDF时页数检查明确记为SKIPPED。

不能盲用：
- 最小化最高栏不保证视觉平衡或论证顺序最优。
- 海报阈值、单页要求不可移植到双栏论文。
- 建议补充内容不能变成自动杜撰或为了填空白增加赘述。

证据范围：实际Typst实现和Python检查器；主要适用海报，未证明对任意论文PDF有效。

## elsevier-floats

固定版本：`83cec1d9835e95b65aced34e018144847fa8dbaf`。
- [SKILL.md](https://github.com/huozuilv/Elsevier-LaTeX-Floats/blob/83cec1d9835e95b65aced34e018144847fa8dbaf/SKILL.md)

可吸收：
- 先识别文档类、编译器、单/双栏及浮动队列，再局部修复。
- 将“过多强制浮动/屏障导致恶化”作为诊断分支，重编译后查看相邻页。

不能盲用：
- 无LICENSE，不能按开源许可复制其skill文本或代码；本项目只独立表达通用方法。
- Overleaf pdfLaTeX权威、禁止特定位置FloatBarrier和0.56正文高度是模板语境，不能泛化。
- 缩图必须重新检查最终字号；减少高度不应破坏内容可读性。

证据范围：特定Elsevier模板经验性文字skill；未见对照实验或通用布局引擎。

## connecting-the-dots

[作者论文 v1](https://arxiv.org/abs/2602.16895v1)；[全文](https://arxiv.org/html/2602.16895v1)。

可吸收：
- 以具体图中元素及相关正文为关系单位，区分直接引用与其他相关段落。
- 检查阅读时的来回寻找成本；可将图、正文摘录及页码并排呈现作为审查证据。

不能盲用：
- 这是一整套交互阅读界面的研究，不是浮动体位置修复器，也未验证“超过一页必差”等阈值。
- 最终比较研究18人；搜索和常规超链接被关闭。整套系统测验得分改善不能归因于物理距离单一因素。
- 未发现完成时间或认知负荷的确定差异，不能宣传降低二者。

证据范围：阅读作者论文；原型、用户研究与局限可核验，未复现实验。

## 整合实施建议

- 每项检查记录 evidence_type：render_measurement、source_measurement、visual_observation、metadata_declaration、heuristic 或 unchecked；声明不能升级为实测。
- 图文关联保存全部引用位置；语义判别首次实质解释段落与导航性提及，分别报告距离，不能只以第一次出现编号优化。
- 规则按模板/载体配置；硬错误（裁切、遮挡、失效链接）与阅读负担提示（远距离、留白、密度）分开。
- 修复有可见证据闭环：源文件diff、输出hash、原页和邻页检查、全篇回归；缺少编译器只能给建议并记未验证。
- 覆盖范围用检查矩阵而非笼统“全部通过”：PDF中可取证、需视觉确认、需源文件或数据、未实施四类。
- 以官方模板优先的局部修复为默认；不得为塞进页面改数值精度、删数据、移除必要图注、过度缩字。

## 许可与新颖性判断

本次没有复制任何第三方实现。四个MIT仓库可按条款复用；无许可证仓库仅研究通用问题与方法；论文以引用和独立概括为主。已有工作已覆盖首次引用距离、视觉复查、浮动队列和多面板检查，因此不应宣称这些检查本身是新功能。更清楚的产品贡献是统一证据格式、减少误报、支持例外、记录检查覆盖度，并用可重跑样例验证。

## 2025 官方规范补充

- [NeurIPS 2025 Call for Papers](https://nips.cc/Conferences/2025/CallForPapers)：要求使用该年样式，正文、参考文献和补充材料的页数范围不同；不能为紧凑擅自缩字体/边距。这支持“实际模板约束优先”，不意味着本 skill 已自动实现 NeurIPS 合规检查。
- [CHI 2025 Publication Ready Author Instructions](https://chi2025.acm.org/for-authors/publication-ready-author-instructions/)：图表可访问描述属于交付要求；正文、图注和可访问描述应分别核对。不能仅看页面漂亮就宣称可访问性通过。

以上是特定年份的官方要求示例。审查其他年份/会议时，应核对当年的实际规则，不把本段硬编码为全局标准。
