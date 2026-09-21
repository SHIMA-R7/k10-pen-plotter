# 接続確認: IDCODE、フラッシュ容量、オプションバイト(RDP)を読むだけ。書き込みなし。
$ocd = if ($env:OPENOCD) { $env:OPENOCD } else { "openocd" }   # xPack OpenOCD 等。PATH に無ければ環境変数 OPENOCD にフルパス
& $ocd -f "$PSScriptRoot\openocd_k10.cfg" `
  -c "init" -c "halt" `
  -c "echo {--- flash size (KB, low 16bit) ---}" -c "mdw 0x1FFFF7E0 1" `
  -c "echo {--- unique ID ---}" -c "mdw 0x1FFFF7E8 3" `
  -c "echo {--- option bytes 0x1FFFF800 ---}" -c "mdw 0x1FFFF800 4" `
  -c "echo {--- FMC_OBSTAT (bit1 = readout protect) ---}" -c "mdw 0x4002201C 1" `
  -c "echo {--- vector table @0x08000000 / @0x08004000 ---}" -c "mdw 0x08000000 2" -c "mdw 0x08004000 2" `
  -c "resume" -c "shutdown"
