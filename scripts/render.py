#!/usr/bin/env python3
"""逐页把 .pptx 渲染成 PNG —— 纯用 macOS 自带 qlmanage，不需要 LibreOffice。

背景：qlmanage 只能渲染 pptx 的第一页。
绕法：每页重建一份「只含该页」的临时副本，单独渲染，再拼成完整的一页一张图。
代价：每页起一次进程，比 LibreOffice 慢（约 1~2 秒/页）。
运行环境：macOS 和 Python 3，无第三方 Python 依赖。

用法:
    render.py deck.pptx                  # 输出到 ./deck_slides/
    render.py deck.pptx -o out/          # 指定输出目录
    render.py deck.pptx -o out/ -s 2000  # 指定渲染宽度（像素，默认 1600）
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

SLDIDLST_RE = re.compile(r"<p:sldIdLst>(.*?)</p:sldIdLst>", re.S)
SLDID_RE = re.compile(r"<p:sldId\b[^>]*/>")


def read_sld_ids(zf):
    """从已打开的 pptx 里抽出 <p:sldIdLst> 中的所有 <p:sldId> 元素。"""
    xml = zf.read("ppt/presentation.xml").decode("utf-8")
    m = SLDIDLST_RE.search(xml)
    if not m:
        raise SystemExit(
            "错误：ppt/presentation.xml 里找不到 <p:sldIdLst>，"
            "这可能不是合法的 .pptx 文件。"
        )
    return xml, SLDID_RE.findall(m.group(1))


def write_single_slide(src, xml, sld_id, dst):
    """把 src 复制成 dst，但 <p:sldIdLst> 里只留下 sld_id 这一页。"""
    new_xml = SLDIDLST_RE.sub(f"<p:sldIdLst>{sld_id}</p:sldIdLst>", xml, count=1)
    with zipfile.ZipFile(src) as zin, \
         zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "ppt/presentation.xml":
                data = new_xml.encode("utf-8")
            zout.writestr(item, data)


def qlmanage_render(pptx, workdir, width):
    """调 qlmanage 渲染单页 pptx，返回生成的 PNG 路径（失败返回 None）。"""
    before = set(os.listdir(workdir))
    result = subprocess.run(
        ["qlmanage", "-t", "-s", str(width), "-o", workdir, pptx],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"qlmanage 退出码 {result.returncode}: {result.stderr.strip() or result.stdout.strip()}")
    for name in set(os.listdir(workdir)) - before:
        if name.endswith(".png"):
            return os.path.join(workdir, name)
    return None


def main():
    ap = argparse.ArgumentParser(
        description="逐页把 .pptx 渲染成 PNG（基于 macOS 自带 qlmanage）"
    )
    ap.add_argument("pptx", help="输入的 .pptx 文件")
    ap.add_argument("-o", "--outdir", help="输出目录（默认 <文件名>_slides/）")
    ap.add_argument("-s", "--width", type=int, default=1600,
                    help="渲染宽度像素，默认 1600")
    args = ap.parse_args()
    if args.width <= 0:
        ap.error("渲染宽度必须大于 0")

    src = os.path.abspath(args.pptx)
    if not os.path.isfile(src):
        raise SystemExit(f"错误：找不到文件 {src}")
    if not src.lower().endswith(".pptx"):
        raise SystemExit(
            "错误：只支持 .pptx。老式 .ppt 请先用 WPS/PowerPoint 另存为 .pptx。"
        )

    outdir = os.path.abspath(
        args.outdir or os.path.splitext(os.path.basename(src))[0] + "_slides"
    )
    os.makedirs(outdir, exist_ok=True)

    try:
        with zipfile.ZipFile(src) as zf:
            xml, sld_ids = read_sld_ids(zf)
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError) as exc:
        raise SystemExit(f"错误：无法读取 PPTX：{exc}")
    total = len(sld_ids)
    if not total:
        raise SystemExit("错误：未找到幻灯片引用")
    print(f"共 {total} 页，输出到 {outdir}")

    workdir = tempfile.mkdtemp(prefix="pptx_preview_")
    written = []
    try:
        for i, sld_id in enumerate(sld_ids):
            tmp_pptx = os.path.join(workdir, f"p{i}.pptx")
            write_single_slide(src, xml, sld_id, tmp_pptx)
            try:
                png = qlmanage_render(tmp_pptx, workdir, args.width)
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
                print(f"  第 {i + 1} 页渲染失败：{exc}", file=sys.stderr)
                continue
            if not png:
                print(f"  第 {i + 1} 页渲染失败，跳过", file=sys.stderr)
                continue
            dst = os.path.join(outdir, f"slide-{i + 1:02d}.png")
            shutil.move(png, dst)
            written.append(dst)
            print(f"  [{i + 1}/{total}] {os.path.basename(dst)}")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print(f"\n完成：{len(written)}/{total} 页")
    return 0 if len(written) == total else 1


if __name__ == "__main__":
    sys.exit(main())
