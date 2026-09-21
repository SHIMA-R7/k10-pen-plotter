# 純正ファームのバックアップ: フラッシュ128KB全体 + オプションバイトを2回読み、ハッシュを照合する。書き込みなし。
$ocd = if ($env:OPENOCD) { $env:OPENOCD } else { "openocd" }   # xPack OpenOCD 等。PATH に無ければ環境変数 OPENOCD にフルパス
$out = "$PSScriptRoot\dump"
New-Item -ItemType Directory -Force $out | Out-Null
foreach ($i in 1, 2) {
  & $ocd -f "$PSScriptRoot\openocd_k10.cfg" `
    -c "init" -c "halt" `
    -c "dump_image {$out/k10_flash_$i.bin} 0x08000000 0x20000" `
    -c "dump_image {$out/k10_optbytes_$i.bin} 0x1FFFF800 0x10" `
    -c "dump_image {$out/k10_sysinfo_$i.bin} 0x1FFFF7E0 0x20" `
    -c "resume" -c "shutdown" 2>&1 | Select-String 'dumped|Error'
}
Get-ChildItem $out | ForEach-Object { '{0,-24} {1,7}  {2}' -f $_.Name, $_.Length, (Get-FileHash $_.FullName).Hash }
