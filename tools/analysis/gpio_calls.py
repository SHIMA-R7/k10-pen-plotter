# 純正ファーム内の GPIO ライブラリ呼び出しを列挙し、引数(ポート/モード/ピン)を定数追跡で復元する
import struct, sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_OPT_ON
from capstone.arm import ARM_OP_IMM, ARM_OP_REG, ARM_OP_MEM, ARM_REG_PC

IMG = sys.argv[1] if len(sys.argv) > 1 else r"..\dump\k10_flash_1.bin"
d = open(IMG, "rb").read()
BASE = 0x08000000
START, END = 0x08004000, 0x0801CE98

PORTS = {0x40010800: "A", 0x40010C00: "B", 0x40011000: "C", 0x40011400: "D"}
FUNCS = {0x8012940: "init", 0x8012a0e: "set", 0x8012a14: "reset", 0x8012a1a: "write", 0x8012a2a: "read"}
MODES = {0x00: "AIN", 0x04: "IN_FLOAT", 0x28: "IPD", 0x48: "IPU", 0x10: "OUT_PP", 0x14: "OUT_OD", 0x18: "AF_PP", 0x1C: "AF_OD"}

md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
md.detail = True
md.skipdata = True


def u32(a):
    o = a - BASE
    return struct.unpack_from("<I", d, o)[0] if 0 <= o < len(d) - 3 else None


def pins(mask):
    return ",".join(str(b) for b in range(16) if mask >> b & 1) if mask is not None else "?"


def port(v):
    return PORTS.get(v, hex(v) if v is not None else "?")


results = []
regs = {}
func_start = START
for ins in md.disasm(d[START - BASE:END - BASE], START):
    m = ins.mnemonic
    if m.startswith(".") or m.startswith("byte"):
        regs = {}
        continue
    ops = ins.operands
    if m.startswith("push"):
        regs = {}
        func_start = ins.address
    try:
        if m in ("mov", "movs", "mov.w", "movw") and len(ops) == 2 and ops[0].type == ARM_OP_REG:
            dst = ops[0].reg
            if ops[1].type == ARM_OP_IMM:
                regs[dst] = ops[1].imm & 0xFFFFFFFF
            elif ops[1].type == ARM_OP_REG:
                regs[dst] = regs.get(ops[1].reg)
        elif m == "movt" and ops[0].type == ARM_OP_REG:
            lo = regs.get(ops[0].reg)
            regs[ops[0].reg] = ((ops[1].imm & 0xFFFF) << 16) | (lo & 0xFFFF) if lo is not None else None
        elif m.startswith("ldr") and len(ops) == 2 and ops[1].type == ARM_OP_MEM and ops[1].mem.base == ARM_REG_PC:
            addr = ((ins.address + 4) & ~3) + ops[1].mem.disp
            regs[ops[0].reg] = u32(addr)
        elif m in ("bl", "blx", "b.w", "b") and ops and ops[0].type == ARM_OP_IMM and ops[0].imm in FUNCS:
            f = FUNCS[ops[0].imm]
            r = [regs.get(x) for x in (66, 67, 68, 69)]  # r0..r3
            results.append((ins.address, func_start, f, r))
            if m in ("bl", "blx"):
                for x in (66, 67, 68, 69, 70 + 8):
                    regs.pop(x, None)
        elif m.startswith("str") and len(ops) == 2 and ops[1].type == ARM_OP_MEM:
            b = regs.get(ops[1].mem.base)
            if b is not None and (b & ~0x1F) in PORTS and False:
                pass
            for pb in PORTS:
                if b is not None and pb <= b + ops[1].mem.disp < pb + 0x20:
                    off = b + ops[1].mem.disp - pb
                    kind = {0x10: "set(direct)", 0x14: "reset(direct)", 0x0C: "OCTL(direct)", 0: "CTL0(direct)", 4: "CTL1(direct)"}.get(off, f"+{off:#x}")
                    results.append((ins.address, func_start, kind, [pb, regs.get(ops[0].reg), None, None]))
            if ops[0].type == ARM_OP_REG and m == "str":
                pass
        elif ops and ops[0].type == ARM_OP_REG and m not in ("cmp", "cmn", "tst", "teq") and not m.startswith("str") and not m.startswith("b") and not m.startswith("push") and not m.startswith("it"):
            regs[ops[0].reg] = None
        if m in ("bl", "blx") and not (ops and ops[0].type == ARM_OP_IMM and ops[0].imm in FUNCS):
            for x in (66, 67, 68, 69):
                regs.pop(x, None)
    except Exception:
        regs = {}

for addr, fs, f, r in results:
    if f == "init":
        print(f"{addr:08x} fn@{fs:08x} init  P{port(r[0])} pins[{pins(r[3])}] mode={MODES.get(r[1], r[1])} speed={r[2]}")
    elif f in ("set", "reset", "read"):
        print(f"{addr:08x} fn@{fs:08x} {f:5s} P{port(r[0])} pins[{pins(r[1])}]")
    elif f == "write":
        print(f"{addr:08x} fn@{fs:08x} write P{port(r[0])} pins[{pins(r[1])}] val={r[2]}")
    else:
        print(f"{addr:08x} fn@{fs:08x} {f} P{port(r[0])} val={r[1] if r[1] is None else hex(r[1])}")
