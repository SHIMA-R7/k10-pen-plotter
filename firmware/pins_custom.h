/**
 * EasyThreed K10 V2.1 (GD32F303CBT6 LQFP48, HR4988SQ x4)
 * 純正ファームのSWDダンプ解析 + 実機レジスタ読み出しで特定したピン定義。
 * 解析メモ: docs/pinmap.md
 *
 * GD32F303CB を STM32F103CB として動かす (ステッパ用 PA9-PA12 は USB/UART と共用のため、USB/UART1 は使えない)
 */
#pragma once

#define BOARD_INFO_NAME      "EasyThreed K10 V2.1"
#define DEFAULT_MACHINE_NAME "K10 Plotter"

#define BOARD_NO_NATIVE_USB

// 外部EEPROMなし → フラッシュ末尾をEEPROM代わりに使う
#define FLASH_EEPROM_EMULATION

// Marlin 既定の STEP=TIM4 / TEMP=TIM2 は VREF PWM (TIM4: PB6-PB8) と衝突するので変更
#define STEP_TIMER 1
#define TEMP_TIMER 2

// JTAG を無効化 (SWD は残す) → PA15 / PB3 / PB4 を GPIO として使う
#define DISABLE_JTAG

//
// 起動直後に安全側へ固定する
//   PB3  ヒーター MOSFET → Low (常時 OFF)
//   PB4  ファン PWM     → Low
//   PA15 用途未確定 (純正は起動時 High にして以後不変。ドライバ SLEEP/RESET 解除と推定)
//   PA1  ステータス LED → 点灯
//   (ボタンの内部プルアップは apply_k10.py で MarlinCore.cpp の初期化マクロを修正して有効化)
//
#define BOARD_PREINIT() do{ \
  __HAL_RCC_AFIO_CLK_ENABLE(); \
  __HAL_AFIO_REMAP_SWJ_NOJTAG(); \
  OUT_WRITE(PB3, LOW);  \
  OUT_WRITE(PB4, LOW);  \
  OUT_WRITE(PA15, HIGH); \
  OUT_WRITE(PA1, HIGH); \
}while(0)

//
// Steppers (純正ファームの stepper init 0x0800B280 / DIR 設定 0x0800AD64 で確認)
//   純正ファーム内部の軸順 (X,Y,Z,E) どおり。シルクとも一致 (2026-09-21 実機で確認: ケーブルは正しく
//   刺さった状態で PC13/PA8 → Y モーター、PA11/PA12 → 押出機モーターが動いた)
//   コネクタ   STEP  DIR
//   X (赤)     PC15  PC14
//   Y (黒)     PC13  PA8    ← ベッド前後
//   Z (青)     PA9   PA10   ← ガントリ昇降。プロッタでは使わない (高さ固定)
//   E (白)     PA11  PA12   ← 押出機モーターを流用してペン上下にする
//   EN は4ドライバ共通 PB9 (Low で有効)
//
// プロッタ構成: Marlin の論理 Z 軸 = ペン上下 = E(白) コネクタのドライバ
//
#define X_STEP_PIN                          PC15
#define X_DIR_PIN                           PC14
#define X_ENABLE_PIN                        PB9

#define Y_STEP_PIN                          PC13
#define Y_DIR_PIN                           PA8
#define Y_ENABLE_PIN                        PB9

#define Z_STEP_PIN                          PA11   // E(白) コネクタ (ペン)
#define Z_DIR_PIN                           PA12
#define Z_ENABLE_PIN                        PB9

//
// Motor current (HR4988 VREF を PWM + RC で生成)
// 純正: 約19.2kHz, PB5/PB6 = 145/750, PB7/PB8 = 127/750
// 100% デューティ = 3.3V → Itrip = 3.3 / (8 * 0.1Ω) ≈ 4125mA を RANGE とすると純正と同じデューティになる
//   800mA → 19.2%, 700mA → 16.9%
// !! VREF ピンとドライバの対応は未確認 (導通確認待ち)。STEP/DIR 同様に Y/E が入れ替わっている可能性もあるので、
//    確定するまでは4本すべてに純正 X/Y と同じ 800mA 相当 (19.2%) を出して、どのドライバにも確実に電流が流れるようにする。
//    EXTRUDERS 0 だと MOTOR_CURRENT_PWM_E_PIN は pins_postprocess.h で消されるので、
//    4本目 (PB7) は XY グループの予備ピン MOTOR_CURRENT_PWM_XY_PIN として出す。
//    M907 X<mA> → PB5/PB6/PB7、M907 Z<mA> → PB8
//
#define MOTOR_CURRENT_PWM_X_PIN             PB5
#define MOTOR_CURRENT_PWM_Y_PIN             PB6
#define MOTOR_CURRENT_PWM_XY_PIN            PB7
#define MOTOR_CURRENT_PWM_Z_PIN             PB8
#define MOTOR_CURRENT_PWM_RANGE             4125
#define MOTOR_CURRENT_PWM_FREQUENCY         19200
#ifndef DEFAULT_PWM_MOTOR_CURRENT
  #define DEFAULT_PWM_MOTOR_CURRENT { 800, 800, 0 }   // XY(PB5,PB6,PB7), Z(PB8), E(なし) (mA)
#endif

//
// Endstops: K10 にはエンドストップ入力がない。空きピン(PA0/PB2/PB11)を仮に割り当てる
//
#define X_STOP_PIN                          PA0
#define Y_STOP_PIN                          PB2
#define Z_STOP_PIN                          PB11

//
// Temperature (プロッタでは未使用。定義だけ残す)
//
#define TEMP_0_PIN                          PA2
#define HEATER_0_PIN                        PB3
#define FAN0_PIN                            PB4

//
// Status LED
//
#define LED_PIN                             PA1

//
// SD card (SPI1: PA5 SCK / PA6 MISO / PA7 MOSI)
//
#define SD_DETECT_PIN                       PA3
#define SD_SS_PIN                           PA4
#define SD_SCK_PIN                          PA5
#define SD_MISO_PIN                         PA6
#define SD_MOSI_PIN                         PA7
#define SDSS                                SD_SS_PIN
#define SD_DETECT_STATE                     LOW

//
// 裏面ボタン S3-S9 (入力プルアップ)。どのボタンがどのピンかは動的解析で確定する
//   PB0, PB1, PB10, PB12, PB13, PB14, PB15
//
