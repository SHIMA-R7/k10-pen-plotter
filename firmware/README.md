# ファームウェアのビルド

素の **Marlin 2.1.2.8** に、このフォルダの設定とパッチを当ててビルドします。

| ファイル | 内容 |
|---|---|
| `apply_k10.py` | Configuration.h / Configuration_adv.h の変更、Marlin 本体の小パッチ2件、ピン定義と env の追加を行う。元ファイルは `.orig` に退避され、何度実行しても同じ結果になる |
| `pins_custom.h` | K10 V2.1 のピン定義 (`BOARD_CUSTOM` で読み込まれる) |
| `buttons_block.h` | 本体ボタンの G-code (`CUSTOM_USER_BUTTONS`) |
| `env_k10.ini` | PlatformIO の env (`custom`)。0x08004000 に配置 |
| `prebuilt/k10_plotter_marlin.bin` | ビルド済みバイナリ |

## 手順

```bash
# 1. Marlin 2.1.2.8 を取得して展開 (パスに日本語やスペースを含まない場所で)
#    https://github.com/MarlinFirmware/Marlin/archive/refs/tags/2.1.2.8.zip
# 2. 設定を適用
python apply_k10.py path/to/Marlin-2.1.2.8
# 3. ビルド
cd path/to/Marlin-2.1.2.8
pio run -e custom
# → .pio/build/custom/firmware.bin を tools/swd/flash_marlin.ps1 -Bin で書き込む
```

## PlatformIO のダウンロードが遅い場合

PlatformIO レジストリのミラーが極端に遅い環境 (約20KB/s) では、以下を GitHub から取得してローカルパッケージにできます。

| パッケージ | 取得元 |
|---|---|
| toolchain-gccarmnoneeabi | xPack arm-none-eabi-gcc 9.2.1-1.1 |
| framework-arduinoststm32 | stm32duino/Arduino_Core_STM32 1.9.0 |
| framework-cmsis | ARM-software/CMSIS_5 5.5.1 |

- それぞれのフォルダに `package.json` (`name` と `version`: 1.90201.191206 / 4.10900.200819 / 2.50501.200527) を置く
- `framework-arduinoststm32/CMSIS` を `framework-cmsis` へのジャンクション (リンク) にする
- CMSIS_5 の `CMSIS/DSP/Lib/GCC/libarm_cortexM3l_math.a` は Git LFS のポインタなので、空のアーカイブ (`!<arch>\n`) に置き換える
- `env_k10.ini` の `platform_packages` と `custom_gcc` のコメントを外してパスを書き換える

## 主な設定値

- 軸: X = PC15/PC14, Y = PC13/PA8, Z (ペン) = PA11/PA12 (E コネクタ), EN = PB9
- steps/mm: X 606, Y 606, Z 649 / 最大速度 20, 20, 6 mm/s / 加速度 300, 300, 100 mm/s²
- 向き: `INVERT_X_DIR true`, `INVERT_Y_DIR false`, `INVERT_Z_DIR false`
- モーター電流: PB5/PB6/PB7/PB8 に PWM 19.2kHz、800mA 相当 (デューティ 19.2%)。`MOTOR_CURRENT_PWM_RANGE 4125`
- `EXTRUDERS 0`, ヒーター (PB3) は起動時に Low 固定
- シリアル: `SERIAL_PORT 1` (PA9/PA10 = 未使用のガントリ Z ドライバの線。外部には出ていない)
- ソフトウェアエンドストップ無効 (原点センサーなし)
