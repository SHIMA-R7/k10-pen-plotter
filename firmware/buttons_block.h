#define CUSTOM_USER_BUTTONS
#if ENABLED(CUSTOM_USER_BUTTONS)
  // K10 V2.1 のボタン (動的解析で確定)。押下で Low
  //   ▷ = PB10 / 裏面 S3 = PB0, S4 = PB1, S6 = PB12, S7 = PB13, S8 = PB14, S9 = PB15
  // ペン機構: ラック&ピニオン + フローティングペン (戻しバネなし)。Z0 = ペン下げ / Z7 = ペン上げ
  // 使い方: 電源OFFで X/Y を「奥」側の端まで手で押し当てる (ペン先 = 紙の右手前の角) → 電源ON →
  //         S8/S9 でペン先をちょうど紙に乗る位置へ → ▷ で その位置を X90 Y0 Z0 にして SD の plot.gco を描画開始
  //         (描画範囲は X0..90 / Y0..90。X+ = 紙に対して右、Y+ = 紙に対して奥 が前提)

  #define BUTTON1_PIN           PB10      // ▷ 描画開始
  #define BUTTON1_HIT_STATE     LOW
  #define BUTTON1_WHEN_PRINTING false
  #define BUTTON1_GCODE         "G92 X90 Y0 Z0\nM23 plot.gco\nM24"
  #define BUTTON1_DESC          "Plot"

  #define BUTTON2_PIN           PB0       // S3: X -5mm
  #define BUTTON2_HIT_STATE     LOW
  #define BUTTON2_WHEN_PRINTING false
  #define BUTTON2_GCODE         "G91\nG0 X-5 F600\nG90"
  #define BUTTON2_DESC          "X-"

  #define BUTTON3_PIN           PB1       // S4: X +5mm
  #define BUTTON3_HIT_STATE     LOW
  #define BUTTON3_WHEN_PRINTING false
  #define BUTTON3_GCODE         "G91\nG0 X5 F600\nG90"
  #define BUTTON3_DESC          "X+"

  #define BUTTON4_PIN           PB12      // S6: Y -5mm
  #define BUTTON4_HIT_STATE     LOW
  #define BUTTON4_WHEN_PRINTING false
  #define BUTTON4_GCODE         "G91\nG0 Y-5 F600\nG90"
  #define BUTTON4_DESC          "Y-"

  #define BUTTON5_PIN           PB13      // S7: Y +5mm
  #define BUTTON5_HIT_STATE     LOW
  #define BUTTON5_WHEN_PRINTING false
  #define BUTTON5_GCODE         "G91\nG0 Y5 F600\nG90"
  #define BUTTON5_DESC          "Y+"

  #define BUTTON6_PIN           PB14      // S8: Z +0.5mm (ペン上げ方向)
  #define BUTTON6_HIT_STATE     LOW
  #define BUTTON6_WHEN_PRINTING false
  #define BUTTON6_GCODE         "G91\nG0 Z0.5 F300\nG90"
  #define BUTTON6_DESC          "Pen up"

  #define BUTTON7_PIN           PB15      // S9: Z -0.5mm (ペン下げ方向)
  #define BUTTON7_HIT_STATE     LOW
  #define BUTTON7_WHEN_PRINTING false
  #define BUTTON7_GCODE         "G91\nG0 Z-0.5 F300\nG90"
  #define BUTTON7_DESC          "Pen down"
#endif
