"""
線画ビットマップ → センターライン SVG (ペンプロッタ用)
    python img2svg_centerline.py 入力画像 [-o 出力.svg] [--threshold 160] [--min-len 8]
輪郭トレース (potrace 等) だと1本の線が縁取りの二重線になるので、
二値化 → 細線化 (skeletonize) → 骨格をたどって折れ線化 → 簡略化 して「線の中心1本」にする。
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from skimage.morphology import skeletonize, remove_small_objects, remove_small_holes
from skimage.measure import approximate_polygon

NB = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def load_ink(path, threshold):
    g = np.asarray(Image.open(path).convert("L"))
    ink = g < threshold
    ink = remove_small_objects(ink, max_size=20)          # ゴミ点
    ink = remove_small_holes(ink, max_size=30)            # 線の中の小さな白抜け (骨格に小ループができるのを防ぐ)
    return ink


def trace(skel):
    H, W = skel.shape
    pts = set(zip(*np.nonzero(skel)))

    def nbrs(p):
        y, x = p
        return [(y + dy, x + dx) for dy, dx in NB if (y + dy, x + dx) in pts]

    deg = {p: len(nbrs(p)) for p in pts}
    nodes = {p for p, d in deg.items() if d != 2}
    used = set()                                  # たどった辺 (画素ペア)
    paths = []

    def walk(start, nxt):
        path = [start, nxt]
        used.add(frozenset((start, nxt)))
        prev, cur = start, nxt
        while cur not in nodes:
            cand = [q for q in nbrs(cur) if q != prev and frozenset((cur, q)) not in used]
            if not cand:
                break
            prev, cur = cur, cand[0]
            used.add(frozenset((prev, cur)))
            path.append(cur)
            if cur == start:
                break
        return path

    for n in nodes:
        for q in nbrs(n):
            if frozenset((n, q)) not in used:
                paths.append(walk(n, q))
    # 端点も分岐もない純粋なループ
    for p in pts:
        for q in nbrs(p):
            if frozenset((p, q)) not in used:
                paths.append(walk(p, q))
    return paths, deg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("-o", "--out", type=Path)
    ap.add_argument("--threshold", type=int, default=160, help="これより暗い画素を線とみなす (0-255)")
    ap.add_argument("--min-len", type=int, default=8, help="これより短い『ヒゲ』(片端が端点の枝) を捨てる [px]")
    ap.add_argument("--simplify", type=float, default=0.8, help="折れ線簡略化の許容誤差 [px]")
    a = ap.parse_args()

    ink = load_ink(a.image, a.threshold)
    skel = skeletonize(ink)
    paths, deg = trace(skel)

    kept = []
    for p in paths:
        spur = deg.get(p[0]) == 1 or deg.get(p[-1]) == 1
        if spur and len(p) < a.min_len:
            continue
        if len(p) < 2:
            continue
        arr = np.array([(x, y) for y, x in p], dtype=float)
        arr = approximate_polygon(arr, a.simplify)
        kept.append(arr)

    H, W = ink.shape
    out = a.out or a.image.with_suffix(".svg")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}px" height="{H}px" viewBox="0 0 {W} {H}">\n')
        f.write('<g fill="none" stroke="black" stroke-width="1">\n')
        for arr in kept:
            f.write('<polyline points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in arr) + '"/>\n')
        f.write("</g>\n</svg>\n")
    total = sum(np.linalg.norm(np.diff(arr, axis=0), axis=1).sum() for arr in kept)
    print(f"{a.image.name}: {W}x{H}px, 線 {len(kept)} 本, 総延長 {total:.0f}px → {out}")


if __name__ == "__main__":
    main()
