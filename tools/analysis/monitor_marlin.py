# プロッタ版 Marlin の内部状態を CPU を止めずに監視する (OpenOCD TCL ポート 6666)
# アドレスは fw\k10_plotter_marlin.elf の nm 結果
import socket, struct, time, sys

COUNT_POSITION = 0x20001314    # int32 x3 (X, Y, Z) 実際に出したステップ数
CURRENT_POSITION = 0x20000D64  # float x3 (mm)
GPIOA_OCTL, GPIOB_OCTL, GPIOC_OCTL = 0x4001080C, 0x40010C0C, 0x4001100C
GPIOB_ISTAT = 0x40010C08
BUTTONS = {10: "▷", 0: "S3", 1: "S4", 12: "S6", 13: "S7", 14: "S8", 15: "S9"}


class Ocd:
    def __init__(self):
        self.s = socket.create_connection(("127.0.0.1", 6666))

    def cmd(self, c):
        self.s.sendall(c.encode() + b"\x1a")
        b = b""
        while not b.endswith(b"\x1a"):
            b += self.s.recv(4096)
        return b[:-1].decode()

    def words(self, addr, n):
        out = self.cmd(f"read_memory {addr:#x} 32 {n}").split()
        try:
            return [int(x, 0) for x in out]
        except ValueError:
            raise IOError(" ".join(out))


def as_i32(w):
    return struct.unpack("<i", struct.pack("<I", w))[0]


def as_f32(w):
    return struct.unpack("<f", struct.pack("<I", w))[0]


def sample(o):
    cnt = [as_i32(w) for w in o.words(COUNT_POSITION, 3)]
    pos = [round(as_f32(w), 3) for w in o.words(CURRENT_POSITION, 3)]
    pa, pb, pc = o.words(GPIOA_OCTL, 1)[0], o.words(GPIOB_OCTL, 1)[0], o.words(GPIOC_OCTL, 1)[0]
    ib = o.words(GPIOB_ISTAT, 1)[0]
    pressed = tuple(name for bit, name in BUTTONS.items() if not ib >> bit & 1)
    # EN(PB9), DIR X(PC14), DIR Y(PA8), DIR Z(PA12)
    return tuple(cnt), tuple(pos), pb >> 9 & 1, pc >> 14 & 1, pa >> 8 & 1, pa >> 12 & 1, pressed


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 90
    o = Ocd()
    t0 = time.time()
    last = None
    while time.time() - t0 < dur:
        t = time.time() - t0
        try:
            st = sample(o)
        except IOError as e:
            # 電源断・Pico 抜けなど。復帰するまで待って続行
            print(f"{t:6.2f}s (read failed: {e}) retrying...", flush=True)
            last = None
            time.sleep(1)
            continue
        if st != last:
            cnt, pos, en, dx, dy, dz, pressed = st
            print(f"{t:6.2f}s steps X{cnt[0]:7d} Y{cnt[1]:7d} Z{cnt[2]:6d} | "
                  f"pos {pos[0]:7.2f} {pos[1]:7.2f} {pos[2]:6.2f} | EN(PB9)={en} "
                  f"DIR X(PC14)={dx} Y(PA8)={dy} Z(PA12)={dz} | pressed={list(pressed)}", flush=True)
            last = st
        time.sleep(0.03)


if __name__ == "__main__":
    main()
