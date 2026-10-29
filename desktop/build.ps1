$ErrorActionPreference = 'Stop'
$taskCalendarBuildRoot = Split-Path -Parent $PSScriptRoot
Push-Location $taskCalendarBuildRoot
try {
    & "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:winexe /platform:x64 '/out:Sunny Calendar Demo.exe' /win32icon:calendar-icon.ico /win32manifest:desktop\app.manifest /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Net.Http.dll /reference:Microsoft.Web.WebView2.Core.dll /reference:Microsoft.Web.WebView2.WinForms.dll desktop\SunnyCalendar.cs
    if ($LASTEXITCODE -ne 0) { throw 'Desktop launcher build failed.' }
} finally { Pop-Location }
