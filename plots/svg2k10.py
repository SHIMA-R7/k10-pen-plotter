"""
SVG → K10 ペンプロッタ用 G-code 変換
    python svg2k10.py 入力.svg [-s 90] [-o 出力.gco]
処理: 読み込み → 最大 S×S mm に縮小/拡大 (縦横比維持) → 線の結合・並べ替え (ペン上げ移動を減らす)
      → 左下を原点に配置 → G-code 出力 → プレビュー PNG と所要時間の目安を表示
"""
import argparse, math, re, subprocess, sys, sysconfig
from pathlib import Path

HERE = Path(__file__).parent
VPYPE = Path(sysconfig.get_path("scripts", "nt_user")) / "vpype.exe"
FEED_DRAW, FEED_TRAVEL, FEED_Z = 900 / 60, 1200 / 60, 300 / 60   # mm/s (k10_vpype.toml と合わせる)
PEN_STROKE = 7.0                                                  # Z0 ↔ Z7


def convert(svg: Path, size: float, out: Path):
    cmd = [str(VPYPE), "-c", str(HERE / "k10_vpype.toml"),
           "read", "--no-crop", str(svg),   # 既定のページ境界での切り取りをしない (縁に接した線が消える)
           "linemerge", "--tolerance", "0.2mm",
           "linesort",
           "reloop",
           "linesimplify", "--tolerance", "0.05mm",
           "layout", "--fit-to-margins", "0mm", "--align", "left", "--valign", "bottom", f"{size}x{size}mm",
           "gwrite", "--profile", "k10", str(out)]
    subprocess.run(cmd, check=True)


def analyze(gco: Path, png: Path):
    draw, travel, lifts = [], [], 0
    x = y = 0.0
    z = 4.0
    xs, ys = [], []
    for line in gco.read_text().splitlines():
        m = dict(re.findall(r"([XYZ])(-?\d+\.?\d*)", line.split(";")[0]))
        if not m:
            continue
        nx, ny = float(m.get("X", x)), float(m.get("Y", y))
        if "Z" in m:
            nz = float(m["Z"])
            if nz < z:
                lifts += 1
            z = nz
        if (nx, ny) != (x, y):
            (draw if z <= 0.5 else travel).append(((x, y), (nx, ny)))
            if z <= 0.5:
                xs += [x, nx]; ys += [y, ny]
        x, y = nx, ny
    dlen = sum(math.dist(a, b) for a, b in draw)
    tlen = sum(math.dist(a, b) for a, b in travel)
    secs = dlen / FEED_DRAW + tlen / FEED_TRAVEL + lifts * (2 * (PEN_STROKE / FEED_Z + 0.3) + 0.3)
    print(f"範囲    : X {min(xs):.1f}..{max(xs):.1f}  Y {min(ys):.1f}..{max(ys):.1f} mm")
    print(f"描画長  : {dlen/1000:.2f} m / 空走 {tlen/1000:.2f} m / ペン上下 {lifts} 回")
    print(f"所要時間: 約 {secs/60:.0f} 分 (加減速を除いた目安)")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
    except ImportError:
        return
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.add_collection(LineCollection(travel, colors="#e0a0a0", linewidths=.3, linestyles=":"))
    ax.add_collection(LineCollection(draw, colors="k", linewidths=.5))
    ax.plot([90], [0], "r+", ms=10)
    ax.set_xlim(-5, 105); ax.set_ylim(-5, 105); ax.set_aspect("equal")
    ax.add_patch(plt.Rectangle((0, 0), 100, 100, fill=False, ls="--", lw=.5, ec="gray"))
    ax.set_title(f"{gco.name}  (+ = origin / ▷ position, red dotted = pen-up travel)", fontsize=8)
    fig.savefig(png, dpi=150)
    print(f"プレビュー: {png}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("svg", type=Path)
    ap.add_argument("-s", "--size", type=float, default=90, help="最大サイズ mm (既定 90)")
    ap.add_argument("-o", "--out", type=Path)
    a = ap.parse_args()
    out = a.out or a.svg.with_suffix(".gco")
    if a.size > 100:
        sys.exit("K10 の描画範囲は 100mm 角まで")
    convert(a.svg, a.size, out)
    analyze(out, out.with_suffix(".png"))
    print(f"G-code  : {out}  (SD のルートに plot.gco という名前でコピーして ▷)")
