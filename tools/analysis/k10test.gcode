; K10 dynamic analysis test (stock firmware)
; 各フェーズの間に待ち時間を入れて、SWDモニタのログで区切りが分かるようにする
; heater cable must be DISCONNECTED, thermistor CONNECTED
G4 S10
M106 S128   ; phase1: fan 50%
G4 S15
M106 S255   ; phase2: fan 100%
G4 S15
M107        ; phase3: fan off
G4 S10
M104 S45    ; phase4: heater on (target 45C, cable disconnected)
G4 S20
M104 S0     ; phase5: heater off
G4 S10
M17         ; phase6: steppers enabled
G4 S10
M18         ; phase7: steppers disabled
G4 S10
