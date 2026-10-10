---
name: pptx-quicklook
description: 把 .pptx 逐页渲染成 PNG 图片，用于目视检查排版问题——文字溢出、元素重叠、对齐错位、边距不足、低对比度。当需要「看一眼 PPT 长什么样」、做 PPT 视觉质检，或 Anthropic 的 pptx 技能走到转图片那一步时使用。用 macOS 自带 qlmanage 实现，不需要安装 LibreOffice。
---

# pptx-quicklook

把 `.pptx` 逐页渲染成 PNG，用来做视觉检查。需要 **macOS 和 Python 3**，使用系统自带 `qlmanage`，无第三方 Python 依赖。仅用于视觉初筛，最终排版需在目标软件验收。

## 用法

```bash
python3 scripts/render.py deck.pptx -o out/
```

在本项目目录执行；安装为 Skill 后，Agent 应将脚本路径解析为此 SKILL.md 所在目录下的 `scripts/render.py`。

输出 `out/slide-01.png`、`slide-02.png` …，然后用支持图片查看的工具逐张检查。

参数：

- `-o out/` 输出目录（默认 `<文件名>_slides/`）
- `-s 2000` 渲染宽度像素（默认 1600；调低可提速）

## 什么时候用它

- 做完 PPT 后的**视觉质检**：查文字溢出、元素重叠、对齐、边距、低对比度
- 想看某个 `.pptx` 长什么样，但不想开 WPS / PowerPoint
- Anthropic 的 `pptx` 技能走到 **"Converting to Images"** 那一步时，**用它顶掉 `soffice`（LibreOffice）那套命令**：原来要 `soffice → PDF → pdftoppm`，现在一条命令直接出图
- 同理顶掉 `scripts/thumbnail.py`（那个也依赖 LibreOffice）

## 原理与局限

`qlmanage` 本身只能渲染 pptx 的**第一页**。本脚本的办法是：为每一页重建一份「只含该页」的临时 `.pptx` 副本（改写 `ppt/presentation.xml` 里的 `<p:sldIdLst>`），单独渲染，再拼成 `slide-NN.png`。

**已知局限，用之前心里有数：**

- **慢**：每页起一次进程，约 1~2 秒/页。20 页的 PPT 约半分钟
- **渲染引擎是 Apple 的**，和真实 PowerPoint / WPS 可能存在细微差异——字体替换、复杂特效、动画可能不一致
- **PowerPoint 原生图表可能渲染缺失或为空白**：演示文稿实测中，第 9 页原生柱状图与第 12 页原生环形图在 Quick Look 中均为空白，尽管 OOXML 中相关图表数据、权重和配色信息存在。预览空白不等于源文件损坏，XML 数据完整也不等于通过视觉验收；详情见 [README 的实测记录](README.md#known-limitations--real-world-findings)。
- **不支持 `.ppt` 老格式**，先另存为 `.pptx`
- **只出图片**：不能反向生成 PPT，也不能转 PDF
- **演讲者备注不会出现在图里**（备注本来就不在幻灯片页面上），要读备注用 `markitdown`

## 前置依赖

运行本脚本仅需 macOS 自带的 `qlmanage` 和 Python 3。生成 PPT 或读取演讲者备注的工具不属于本项目运行依赖。

## 关键提醒

- **图表预览缺失时不能判定视觉检查通过**：标记为「预览不完整／需要目标软件验证」，在 PowerPoint / WPS 等目标软件中打开原始 PPTX，确认图表排版、柱状图标签裁切、环形图 15% 标签是否压边等问题。生成 PNG 或 XML 检查通过都不能替代这一步。
- **旧图要先清**：输出目录里残留的上一版 `slide-NN.png` 会和新的混淆，重新渲染前先 `rm -f out/slide-*.png`
- **改了 PPT 必须重渲染**：直接看旧图 = 看的是上一版
- 每页调用设置 60 秒超时；任意页面失败时脚本返回非零退出码。退出码为零仅表示图片生成成功，不表示视觉验收通过。
