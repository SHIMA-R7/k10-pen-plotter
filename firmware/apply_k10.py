"""
Marlin 2.1.2.8 の素の設定に K10 V2.1 ペンプロッタ用の変更を当てるスクリプト。
    python apply_k10.py <Marlinソースのルート>
何度実行しても同じ結果になる (元ファイルは .orig に退避してそこから毎回作り直す)。
"""
import re, shutil, sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "../Marlin-2.1.2.8")
here = Path(__file__).parent


def load(rel):
    p = root / rel
    orig = p.with_suffix(p.suffix + ".orig")
    if not orig.exists():
        shutil.copy(p, orig)
    return p, orig.read_text(encoding="utf-8")


def set_define(txt, name, value=None, enable=True):
    """#define name value を設定 (コメントアウトされていれば外す)。enable=False ならコメントアウト"""
    pat = re.compile(rf"^(\s*)(//\s*)?#define\s+{name}\b.*$", re.M)
    m = pat.search(txt)
    if not m:
        raise SystemExit(f"define not found: {name}")
    if enable:
        line = f"{m.group(1)}#define {name}" + (f" {value}" if value is not None else "")
    else:
        line = f"{m.group(1)}//#define {name}"
    return txt[:m.start()] + line + txt[m.end():]


# ---------------- Configuration.h ----------------
p, t = load("Marlin/Configuration.h")
C = [
    ("MOTHERBOARD", "BOARD_CUSTOM"),
    ("SERIAL_PORT", "1"),                 # USART1 (PA9 TX / PA10 RX) = 使わないガントリZドライバの STEP/DIR 線
    ("BAUDRATE", "115200"),
    ("CUSTOM_MACHINE_NAME", '"K10 Plotter"'),
    ("EXTRUDERS", "0"),
    ("TEMP_SENSOR_0", "0"),
    ("TEMP_SENSOR_BED", "0"),
    ("X_DRIVER_TYPE", "A4988"),
    ("Y_DRIVER_TYPE", "A4988"),
    ("Z_DRIVER_TYPE", "A4988"),
    ("DEFAULT_AXIS_STEPS_PER_UNIT", "{ 606, 606, 649 }"),      # X/Y 純正値 (50mm で実測確認済)。Z = 28BYJ系 1/64 × 1/16μstep ÷ ピニオン m1 z16 (50.27mm/rev) の計算値 → 要校正
    ("DEFAULT_MAX_FEEDRATE", "{ 20, 20, 6 }"),                   # X/Y は 50 だと脱調 (実機 2026-09-21)。Z はギヤードモーターなので遅く
    ("DEFAULT_MAX_ACCELERATION", "{ 300, 300, 100 }"),
    ("DEFAULT_ACCELERATION", "300"),
    ("DEFAULT_TRAVEL_ACCELERATION", "300"),
    ("INVERT_X_DIR", "true"),              # 純正の INVERT フラグは全軸 1。実機で要確認
    ("INVERT_Y_DIR", "false"),             # 実機で Y+ がベッドを奥の端へ押し込む向きだったので反転 (2026-09-22)
    ("INVERT_Z_DIR", "false"),             # Z = E コネクタ (ペン)。実機でペン上下が逆だったので反転 (2026-09-22)
    ("X_BED_SIZE", "100"),
    ("Y_BED_SIZE", "100"),
    ("Z_MAX_POS", "7"),                    # ペンのストローク。Z0 = ペン下げ (▷ を押した位置)、Z7 = ペン上げ
    ("HOMING_FEEDRATE_MM_M", "{ (20*60), (20*60), (10*60) }"),
]
for n, v in C:
    t = set_define(t, n, v)
for n in ["E0_DRIVER_TYPE", "PREVENT_COLD_EXTRUSION", "PIDTEMP", "SHOW_BOOTSCREEN",
          "MIN_SOFTWARE_ENDSTOPS", "MAX_SOFTWARE_ENDSTOPS",   # 原点センサーなし。起動位置/▷押下位置が原点
          "THERMAL_PROTECTION_HOTENDS", "THERMAL_PROTECTION_BED",
          "THERMAL_PROTECTION_CHAMBER", "THERMAL_PROTECTION_COOLER"]:
    t = set_define(t, n, enable=False)
for n in ["SDSUPPORT", "EEPROM_SETTINGS"]:
    t = set_define(t, n)
p.write_text(t, encoding="utf-8")

# ---------------- Configuration_adv.h ----------------
p, t = load("Marlin/Configuration_adv.h")
t = set_define(t, "AXIS_RELATIVE_MODES", "{ false, false, false }")   # EXTRUDERS 0 なので XYZ の3要素
# HR4988 (PC13-15 は低速ピン) 向けにパルス幅と DIR 切替待ちを広めに
t = set_define(t, "MINIMUM_STEPPER_PULSE", "2")
# 戻しバネなし: Z の基準は ▷ を押した位置 (S8/S9 でペン先を紙に合わせてから押す)
# EN は4軸共通。無効化されるとラックが自重で動く可能性あり → 描画後もすぐには無効化しない
t = set_define(t, "DEFAULT_STEPPER_TIMEOUT_SEC", "600")
t = set_define(t, "MINIMUM_STEPPER_PRE_DIR_DELAY", "1000")
t = set_define(t, "MINIMUM_STEPPER_POST_DIR_DELAY", "1000")
# ユーザーボタンのブロックを K10 用に差し替え
blk = re.compile(r"^//#define CUSTOM_USER_BUTTONS\n#if ENABLED\(CUSTOM_USER_BUTTONS\)\n.*?^#endif\n", re.M | re.S)
assert blk.search(t), "CUSTOM_USER_BUTTONS block not found"
t = blk.sub(lambda _: (here / "buttons_block.h").read_text(encoding="utf-8"), t, count=1)
p.write_text(t, encoding="utf-8")

# ---------------- Marlin 本体の小パッチ ----------------
# EXTRUDERS 0 + PWM モーター電流の組み合わせで SP_E_STR が未定義になる不具合 (2.1.2.8) を回避
p, t = load("Marlin/src/gcode/feature/digipot/M907-M910.cpp")
t = t.replace(", SP_E_STR,         stepper.motor_current_setting[2]", ', PSTR(" E"),      stepper.motor_current_setting[2]')
p.write_text(t, encoding="utf-8")

# ユーザーボタンの初期化が AVR 流 (SET_INPUT + WRITE HIGH) で、STM32 ではプルアップが有効にならない不具合を修正
p, t = load("Marlin/src/MarlinCore.cpp")
old = "SET_INPUT(BUTTON##N##_PIN); WRITE(BUTTON##N##_PIN, !BUTTON##N##_HIT_STATE);"
assert old in t, "button init macro not found"
t = t.replace(old, "if (BUTTON##N##_HIT_STATE) SET_INPUT_PULLDOWN(BUTTON##N##_PIN); else SET_INPUT_PULLUP(BUTTON##N##_PIN);")
p.write_text(t, encoding="utf-8")

# ---------------- pins / platformio ----------------
shutil.copy(here / "pins_custom.h", root / "Marlin/src/pins/pins_custom.h")

p, t = load("platformio.ini")
t = re.sub(r"^default_envs\s*=.*$", "default_envs = custom", t, count=1, flags=re.M)
t += "\n" + (here / "env_k10.ini").read_text(encoding="utf-8")
p.write_text(t, encoding="utf-8")
print("applied to", root.resolve())
