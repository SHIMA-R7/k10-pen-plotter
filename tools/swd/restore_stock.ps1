# 純正ファームへ戻す: dump.ps1 で取った自分の基板のバックアップ (フラッシュ128KB全体) を書き戻して照合する。
# 純正ファームは EasyThreed の著作物なのでこのリポジトリには含まれていない。
param([Parameter(Mandatory)][string]$Image, [string]$ExpectedSha256)
$ocd = if ($env:OPENOCD) { $env:OPENOCD } else { "openocd" }   # xPack OpenOCD 等。PATH に無ければ環境変数 OPENOCD にフルパス
$img = (Resolve-Path $Image).Path
if ((Get-Item $img).Length -ne 131072) { throw "128KB のフラッシュ全体ダンプではない: $img" }
if ($ExpectedSha256 -and (Get-FileHash $img).Hash -ne $ExpectedSha256) { throw "backup hash mismatch: $img" }
$imgFwd = $img -replace '\\', '/'
& $ocd -f "$PSScriptRoot\openocd_k10.cfg" `
  -c "init" -c "reset halt" `
  -c "flash write_image erase {$imgFwd} 0x08000000" `
  -c "verify_image {$imgFwd} 0x08000000" `
  -c "reset run" -c "shutdown"
