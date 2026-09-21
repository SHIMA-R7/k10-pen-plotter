"""
K10 ペンリフト用 ピニオン & ラック (STEP 出力)
  モーター: 24BYJ28 / 28BYJ 系 ギヤードステッピング (出力軸 φ5 / 2面カット)
  インボリュート歯形、モジュール 1.0、圧力角 20°
    python make_gears.py      → pinion.step / rack.step / check.png
寸法はすべて mm。パラメータを変えて再実行すれば作り直せる。
"""
import math
from pathlib import Path
import cadquery as cq

OUT = Path(__file__).parent

# ---- 共通 ----
MODULE = 1.0            # FDM (0.4mm ノズル) で無理なく刷れる大きさ
PRESSURE_DEG = 20.0
BACKLASH = 0.15         # 歯厚を合計でこれだけ薄くする (ピニオン/ラックで半分ずつ)
FACE_WIDTH = 6.0        # 歯幅

# ---- ピニオン ----
Z_PINION = 16           # ピッチ円 φ16 → 1回転 50.27mm
BORE_D = 5.1            # 軸 φ5 + クリアランス
BORE_FLAT = 3.1         # 2面カット 対辺 3.0 + クリアランス (28BYJ-48 標準)

# ---- ラック ----
RACK_TEETH = 14         # 14 × π ≈ 44mm
RACK_BODY = 5.0         # 歯底から下の肉厚

a = math.radians(PRESSURE_DEG)
inv = lambda x: math.tan(x) - x


def pinion_profile(n_flank=24, n_arc=6):
    rp = MODULE * Z_PINION / 2
    rb = rp * math.cos(a)
    ra = rp + MODULE
    rf = rp - 1.25 * MODULE
    s = math.pi * MODULE / 2 - BACKLASH / 2          # ピッチ円上の歯厚
    psi = s / (2 * rp)                               # 歯厚の半角

    def half_angle(r):
        r = max(r, rb)
        return psi + inv(a) - inv(math.acos(rb / r))

    pts = []
    pitch_ang = 2 * math.pi / Z_PINION
    rs = [rf + (ra - rf) * i / n_flank for i in range(n_flank + 1)]
    for k in range(Z_PINION):
        c = k * pitch_ang
        right = [(r, c - half_angle(r)) for r in rs]           # 歯元→歯先
        left = [(r, c + half_angle(r)) for r in reversed(rs)]  # 歯先→歯元
        tip0, tip1 = right[-1][1], left[0][1]
        tip = [(ra, tip0 + (tip1 - tip0) * i / n_arc) for i in range(1, n_arc)]
        root0 = left[-1][1]
        root1 = (k + 1) * pitch_ang - half_angle(rf)
        root = [(rf, root0 + (root1 - root0) * i / n_arc) for i in range(1, n_arc)]
        for r, t in right + tip + left + root:
            pts.append((r * math.cos(t), r * math.sin(t)))
    return pts


def pinion_wire():
    """歯面をスプライン、歯先/歯底を円弧でつないだ輪郭 (STEP を軽く・滑らかにする)"""
    rp = MODULE * Z_PINION / 2
    rb = rp * math.cos(a)
    ra = rp + MODULE
    rf = rp - 1.25 * MODULE
    psi = (math.pi * MODULE / 2 - BACKLASH / 2) / (2 * rp)
    half = lambda r: psi + inv(a) - inv(math.acos(rb / max(r, rb)))
    P = lambda r, t: (r * math.cos(t), r * math.sin(t))
    r_start = max(rb, rf)
    inv_r = [r_start + (ra - r_start) * i / 12 for i in range(13)]   # インボリュート区間
    step = 2 * math.pi / Z_PINION

    wp = cq.Workplane("XY").moveTo(*P(rf, -half(rf)))
    for k in range(Z_PINION):
        c = k * step
        if rf < rb:                                   # 基礎円より下は放射方向の直線
            wp = wp.lineTo(*P(rb, c - half(rb)))
        wp = wp.spline([P(r, c - half(r)) for r in inv_r[1:]], includeCurrent=True)
        wp = wp.threePointArc(P(ra, c), P(ra, c + half(ra)))
        wp = wp.spline([P(r, c + half(r)) for r in reversed(inv_r[:-1])], includeCurrent=True)
        if rf < rb:
            wp = wp.lineTo(*P(rf, c + half(rf)))
        nxt = c + step - half(rf)
        if k == Z_PINION - 1:
            wp = wp.threePointArc(P(rf, c + step / 2), P(rf, -half(rf)))
        else:
            wp = wp.threePointArc(P(rf, c + step / 2), P(rf, nxt))
    return wp.close()


def make_pinion():
    gear = pinion_wire().extrude(FACE_WIDTH)
    # 軸穴: φBORE_D の円を対辺 BORE_FLAT の帯で切った2面カット形状
    bore = cq.Workplane("XY").circle(BORE_D / 2).extrude(FACE_WIDTH)
    band = cq.Workplane("XY").rect(BORE_D + 2, BORE_FLAT).extrude(FACE_WIDTH)
    return gear.cut(bore.intersect(band))


def rack_profile():
    p = math.pi * MODULE
    h_add, h_ded = MODULE, 1.25 * MODULE
    half_s = (p / 2 - BACKLASH / 2) / 2              # ピッチ線上の歯厚の半分
    t = math.tan(a)
    pts = [(0.0, -h_ded - RACK_BODY)]
    for i in range(RACK_TEETH):
        cx = p / 2 + i * p
        pts += [(cx - half_s - h_ded * t, -h_ded),
                (cx - half_s + h_add * t, h_add),
                (cx + half_s - h_add * t, h_add),
                (cx + half_s + h_ded * t, -h_ded)]
    L = RACK_TEETH * p
    pts += [(L, -h_ded), (L, -h_ded - RACK_BODY)]
    # 先頭の歯の手前に歯底
    pts.insert(1, (0.0, -h_ded))
    return pts


def make_rack():
    # XY 平面に歯形、Z 方向に歯幅。ピッチ線 = Y0、歯は +Y 向き、長さ方向 = X
    return cq.Workplane("XY").polyline(rack_profile()).close().extrude(FACE_WIDTH)


def preview():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    rp = MODULE * Z_PINION / 2
    fig, ax = plt.subplots(figsize=(8, 5))
    # ラックの歯とピニオンの歯がかみ合う位置に並べる (ピニオン中心を ラック歯溝の上 rp の位置)
    rk = rack_profile()
    ax.fill(*zip(*rk), alpha=.35, label="rack")
    cx = math.pi * MODULE * 7                        # ラックの歯溝の中心 (x = n·p)
    ang = -math.pi / 2                               # ピニオンの歯 (0°方向) を真下の歯溝に向ける
    pp = [(cx + x * math.cos(ang) - y * math.sin(ang), rp + x * math.sin(ang) + y * math.cos(ang))
          for x, y in pinion_profile()]
    ax.fill(*zip(*pp), alpha=.35, label="pinion")
    ax.axhline(0, lw=.5, ls="--", c="k")
    ax.set_aspect("equal"); ax.legend(); ax.set_title(f"m{MODULE} z{Z_PINION} / rack {RACK_TEETH}T")
    fig.savefig(OUT / "check.png", dpi=150)


if __name__ == "__main__":
    cq.exporters.export(make_pinion(), str(OUT / "pinion.step"))
    cq.exporters.export(make_rack(), str(OUT / "rack.step"))
    preview()
    rp = MODULE * Z_PINION / 2
    print(f"pinion: pitch d={2*rp:.1f} tip d={2*rp+2*MODULE:.1f} mm, travel/rev={math.pi*2*rp:.2f} mm")
    print(f"rack  : length={RACK_TEETH*math.pi*MODULE:.2f} mm, pitch line = Y0, bottom = Y{-(1.25*MODULE+RACK_BODY):.2f}")
