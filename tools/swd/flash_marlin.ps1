# Marlin (プロッタ版) を SWD で 0x08004000 に書き込む。
# 純正SDブートローダ (0x08000000-0x08003FFF) には触れない。
# 元に戻すときは restore_stock.ps1
param([string]$Bin = "$PSScriptRoot\..\..\firmware\prebuilt\k10_plotter_marlin.bin")
$ocd = if ($env:OPENOCD) { $env:OPENOCD } else { "openocd" }   # xPack OpenOCD 等。PATH に無ければ環境変数 OPENOCD にフルパス
if (-not (Test-Path $Bin)) { throw "not found: $Bin" }
$b = [IO.File]::ReadAllBytes($Bin)
$sp = [BitConverter]::ToUInt32($b, 0); $rst = [BitConverter]::ToUInt32($b, 4)
if (($sp -band 0xFFF00000) -ne 0x20000000 -or $rst -lt 0x08004000 -or $rst -ge 0x08020000) {
  throw ("vector table looks wrong: SP={0:X8} Reset={1:X8} (0x08004000 用にビルドされていない?)" -f $sp, $rst)
}
$binFwd = $Bin -replace '\\', '/'
& $ocd -f "$PSScriptRoot\openocd_k10.cfg" `
  -c "init" -c "reset halt" `
  -c "flash write_image erase {$binFwd} 0x08004000" `
  -c "verify_image {$binFwd} 0x08004000" `
  -c "reset run" -c "shutdown"
