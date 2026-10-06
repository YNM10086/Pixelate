# 在桌面建一个指向源码的快捷方式：改完代码双击就能看效果，不用打包 exe。
#
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1 -Console   # 用带黑框的 python.exe
#   powershell -ExecutionPolicy Bypass -File make_shortcut.ps1 -Remove
#
# 图标指向外部 icon.ico（不嵌进资源），换图标时快捷方式不用重建。

param([switch]$Remove, [switch]$Console)

$ErrorActionPreference = 'Stop'

$proj = Split-Path -Parent $MyInvocation.MyCommand.Path
$name = 'Pixelate'
$lnk  = Join-Path ([Environment]::GetFolderPath('Desktop')) "$name.lnk"

if ($Remove) {
    if (Test-Path -LiteralPath $lnk) {
        Remove-Item -LiteralPath $lnk
        "已删除 $lnk"
    } else {
        "不存在 $lnk"
    }
    return
}

$python = (Get-Command python -ErrorAction Stop).Source
$pyDir  = Split-Path -Parent $python
$exe    = $python
if (-not $Console) {
    $pyw = Join-Path $pyDir 'pythonw.exe'
    if (Test-Path -LiteralPath $pyw) { $exe = $pyw }
}

$sh = New-Object -ComObject WScript.Shell
$s  = $sh.CreateShortcut($lnk)
$s.TargetPath       = $exe
$s.Arguments        = '"{0}"' -f (Join-Path $proj 'mosaic_app.py')
$s.WorkingDirectory = $proj
$s.IconLocation     = '{0},0' -f (Join-Path $proj 'icon.ico')
$s.Description      = "$name — 图片马赛克工具（源码直跑，改完即生效）"
$s.WindowStyle      = 1
$s.Save()

"已创建 $lnk"
foreach ($k in 'TargetPath', 'Arguments', 'WorkingDirectory', 'IconLocation', 'Description') {
    '  {0}: {1}' -f $k, $s.$k
}
'桌面图标可能要等几秒才刷新；不刷新就重登一次。'