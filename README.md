# pptx-quicklook

Render PPTX slides to PNG with macOS Quick Look for a quick visual review.

利用 macOS 自带的 `qlmanage` 将 PPTX 逐页输出为 PNG，供用户或 Agent 快速预览与视觉初筛。运行需要 macOS 和 Python 3，无需安装 LibreOffice；`SKILL.md` 是可选的 Agent 使用入口。

## Quick Start

在项目目录运行：

```bash
python3 scripts/render.py deck.pptx -o out/
```

输出为 `out/slide-01.png`、`out/slide-02.png` 等。可用 `-s 2000` 指定渲染宽度（默认 1600 像素）。重新预览前需清理上一版生成的图片，避免混淆。

脚本按 `ppt/presentation.xml` 中的幻灯片引用顺序，为每页创建临时 PPTX，仅保留该页的幻灯片列表引用，再调用 `qlmanage` 生成图片。输入 PPTX 不被改写，临时文件在处理结束后清理。

## Rebuild with Your Agent

PPTX 是 ZIP/OOXML 文件。读取 `ppt/presentation.xml` 中 `p:sldIdLst` 的引用顺序；对每页复制整个 ZIP，仅将该列表替换为目标页的唯一引用，保留其他资源与关系。对每个临时副本调用 `qlmanage -t -s 1600 -o <临时目录> <副本>`，将 PNG 按原始顺序命名。不要改写源文件，结束时清理临时目录，明确报告失败与超时。

可把这一节交给 Coding Agent：用 Python 标准库实现上述流程，支持输入路径、输出目录和宽度参数，保持输入不变；将结果定位为视觉初筛，并遵守下方原生图表限制。

当前参考实现只识别标准 `p:` 前缀和自闭合的 `p:sldId` 标签；其他等价 XML 写法可能无法识别，不宣称支持所有合法 OOXML 文件。

## Optional Agent Skill

[SKILL.md](SKILL.md) 是可选入口，可由支持 Agent Skills 的工具加载。直接运行 Python 脚本不需要安装 Skill。对外项目和 Skill 名称均为 `pptx-quicklook`；本地目录保留原名，避免影响已有引用。

## Related Work / Prior Art

这一技术技巧已有公开实现，并非本项目首创。以下链接来自此前调查，本轮访问未成功，未重新核验当前代码：

- [Kairos](https://github.com/kr7shnasomani/kairos/blob/main/deck/export.py)：此前记录为逐页 Quick Look 渲染，用于 PDF fallback。
- [PipRail](https://github.com/piprail/piprail/blob/main/.claude/skills/branding/design/deck/preview.mjs)：此前记录为 JSZip 修改列表后的设计预览工作流。
- [Genie Voice Agent](https://github.com/suneelsunkara-db/genie-voice-agent/blob/main/deck-framework/render_preview.py)：此前记录为相似的 Python / OOXML 方案。

本项目选择独立 Recipe 和 Python 标准库参考实现，便于理解和复现，无需绑定 Agent 框架；未复制上述项目代码。现有脚本按项目来源说明为原创，当前文件中未发现第三方版权标记。

## Known Limitations / Real-world Findings

Quick Look 适合快速预览与视觉初筛，不能代替 PowerPoint / WPS 等目标软件的最终排版验收。字体、版式及复杂元素的显示可能与目标软件不同；本工具仅支持 `.pptx`，且每页都需要单独调用 Quick Look。

### 原生图表可能渲染为空白

在一次演示文稿实测中，**第 9 页的原生柱状图与第 12 页的原生环形图均在 macOS Quick Look 预览中显示为空白**。检查 OOXML 后发现，相关图表数据、权重和配色信息存在，但无法通过 Quick Look 确认图表实际排版是否正确，包括柱状图标签是否裁切、环形图的 **15% 标签是否压边**等问题。本记录来自实际使用反馈，所述演示文稿未在本次发布准备中重新渲染。

**Quick Look 对 PowerPoint 原生图表存在渲染缺失的风险。预览空白不等于源文件损坏；XML 数据完整也不等于已经通过视觉验收。**

遇到此类页面，使用者或 Agent 应：

- 将页面标记为 **「预览不完整／需要目标软件验证」**，而不是「视觉检查通过」。
- 在 PowerPoint / WPS 等目标软件中打开原始 PPTX，检查图表、标签裁切及边距等实际显示效果，再给出验收结论。
- 在检查结果中明确记录缺失的图表及尚未验证的排版问题；即使脚本成功生成 PNG，也不能据此认定页面内容完整。

本工具不会自动判定图表是否完整渲染，也不会自动修复此类图表。本次文档补充不引入新的渲染器或自动修复功能。

## Validation

2026-10-10 本地验证（macOS，真实 `qlmanage`，需沙箱外运行）：

- PptxGenJS 生成的三页公开无敏感内容样例：成功输出 3/3 PNG，逐张检查为红／绿／蓝底及 SLIDE 1／2／3，数量、顺序与内容一致；带空格路径正常。
- 重复渲染：输入 SHA-256 不变，临时目录清理后为空，退出码为 0。
- 缺失文件、非正宽度：返回非零并提供错误信息；三页临时副本的 XML 引用顺序检查通过。
- 非零渲染退出码、超时传播及页面失败退出码：使用模拟调用验证通过，与真实渲染验证分开记录。
- 手写最小 OOXML 样例在 Quick Look 中出现超时，不计为渲染通过；未验证 PowerPoint / WPS 生成的其他样例，也未重新验证上述实测演示文稿或原生图表的实际排版。

测试文件、图片与生成工具均在 `/tmp`，不属于公开仓库；PptxGenJS 仅用于制作测试样例，不是运行依赖。

图片生成成功不能证明原生图表或其他复杂对象渲染完整。重新运行前请使用专用输出目录并清理上一版 `slide-*.png`；脚本不自动删除旧图，失败页面可能留下上一版图片。每页调用超时为 60 秒，部分页面失败也返回非零退出码。

## License

代码和文档使用 [MIT License](LICENSE)。
