# OpenOCD の TCL ポート(6666)経由で、CPUを止めずに GPIO/タイマのレジスタを周期的に読み、変化をログに残す
# 事前に: openocd -f openocd_k10.cfg -c init   (haltしない)
import socket, time, sys, csv

REGS = {
    "GPIOA_OCTL": 0x4001080C, "GPIOA_ISTAT": 0x40010808,
    "GPIOB_OCTL": 0x40010C0C, "GPIOB_ISTAT": 0x40010C08,
    "GPIOC_OCTL": 0x4001100C,
    "T2_CHCTL2": 0x40000420, "T2_CV0_PB4": 0x40000434, "T2_CV1_PB5": 0x40000438,
    "T3_CHCTL2": 0x40000820, "T3_CV0_PB6": 0x40000834, "T3_CV1_PB7": 0x40000838, "T3_CV2_PB8": 0x4000083C,
}
TERM = b"\x1a"


class Ocd:
    def __init__(self, host="127.0.0.1", port=6666):
        self.s = socket.create_connection((host, port))

    def cmd(self, c):
        self.s.sendall(c.encode() + TERM)
        buf = b""
        while not buf.endswith(TERM):
            buf += self.s.recv(4096)
        return buf[:-1].decode()

    def read32(self, addr):
        out = self.cmd(f"read_memory {addr:#x} 32 1")
        return int(out.split()[0], 0)


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 240
    ocd = Ocd()
    t0 = time.time()
    last = {}
    with open("monitor_log.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "reg", "old", "new", "changed_bits"])
        while time.time() - t0 < dur:
            for name, addr in REGS.items():
                try:
                    v = ocd.read32(addr)
                except Exception as e:
                    print("read error", name, e)
                    continue
                # PWM出力中のピン(PB4-PB8)の入力読み返しはノイズなので無視
                if name == "GPIOB_ISTAT":
                    v &= ~0x1F0
                if name in last and last[name] != v:
                    diff = last[name] ^ v
                    bits = [b for b in range(32) if diff >> b & 1]
                    t = time.time() - t0
                    print(f"{t:7.2f}s {name:12s} {last[name]:#010x} -> {v:#010x} bits{bits}")
                    w.writerow([f"{t:.2f}", name, hex(last[name]), hex(v), bits])
                    f.flush()
                last[name] = v
            time.sleep(0.05)


if __name__ == "__main__":
    main()
