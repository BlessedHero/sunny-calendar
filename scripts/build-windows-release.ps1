param([string]$OutputDirectory = 'release')
$ErrorActionPreference = 'Stop'
$taskBuildRoot = Split-Path -Parent $PSScriptRoot
Push-Location $taskBuildRoot
try {
    $taskTools = Join-Path $taskBuildRoot '.build-tools'
    $taskOutput = Join-Path $taskBuildRoot $OutputDirectory
    New-Item -ItemType Directory -Force -Path $taskTools,$taskOutput | Out-Null
    function Get-CheckedDownload([string]$Uri,[string]$Destination,[string]$Sha256) {
        Invoke-WebRequest -Uri $Uri -OutFile $Destination
        if ((Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash -ne $Sha256) { throw 'Build dependency checksum mismatch.' }
    }
    Get-CheckedDownload 'https://www.python.org/ftp/python/3.14.10/python-3.14.10-embed-amd64.zip' (Join-Path $taskTools 'python.zip') '90905E64A840557D8C1BC4F5B74DB3D7EE85E3FFB217611CAC1C7813ACEA4159'
    Expand-Archive -LiteralPath (Join-Path $taskTools 'python.zip') -DestinationPath runtime -Force
    Get-CheckedDownload 'https://api.nuget.org/v3-flatcontainer/microsoft.web.webview2/1.0.4314.35/microsoft.web.webview2.1.0.4314.35.nupkg' (Join-Path $taskTools 'webview2.zip') '90778DEB1B77E36292828B4B5833C9255C27533F40E0DDD55891AE718944EDC4'
    $taskSdk = Join-Path $taskTools 'webview2'
    Expand-Archive -LiteralPath (Join-Path $taskTools 'webview2.zip') -DestinationPath $taskSdk -Force
    Copy-Item -LiteralPath (Join-Path $taskSdk 'lib/net462/Microsoft.Web.WebView2.Core.dll') -Destination .
    Copy-Item -LiteralPath (Join-Path $taskSdk 'lib/net462/Microsoft.Web.WebView2.WinForms.dll') -Destination .
    Copy-Item -LiteralPath (Join-Path $taskSdk 'build/native/x64/WebView2Loader.dll') -Destination .
    npm.cmd ci
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
    npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    npm.cmd run test:sites
    if ($LASTEXITCODE -ne 0) { throw 'Existing worker tests failed.' }
    & (Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe') /nologo /target:winexe /platform:x64 '/out:Sunny Calendar Demo.exe' /win32icon:calendar-icon.ico /win32manifest:desktop\app.manifest /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Net.Http.dll /reference:Microsoft.Web.WebView2.Core.dll /reference:Microsoft.Web.WebView2.WinForms.dll desktop\SunnyCalendar.cs
    if ($LASTEXITCODE -ne 0) { throw 'Windows launcher build failed.' }
    $taskPython = Join-Path $taskBuildRoot 'runtime/python.exe'
    & $taskPython scripts/package-release.py --output $taskOutput --source
    if ($LASTEXITCODE -ne 0) { throw 'Clean package checks failed.' }
    $taskVersion = (Get-Content -Raw package.json | ConvertFrom-Json).version
    $taskPayload = Join-Path $taskTools 'payload'
    Expand-Archive -LiteralPath (Join-Path $taskOutput "Sunny-Calendar-Demo-Windows-$taskVersion.zip") -DestinationPath $taskPayload -Force
    $taskBootstrapper = Join-Path $taskPayload 'MicrosoftEdgeWebview2Setup.exe'
    Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $taskBootstrapper
    $taskSignature = Get-AuthenticodeSignature -LiteralPath $taskBootstrapper
    if ($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notmatch 'Microsoft Corporation') { throw 'WebView2 bootstrapper signature verification failed.' }
    $taskInnoSetup = Join-Path $taskTools 'innosetup.exe'
    Get-CheckedDownload 'https://github.com/jrsoftware/issrc/releases/download/is-7_1_1/innosetup-7.1.1-x64.exe' $taskInnoSetup '8A5A6711C3766A6E5FB74F280BA0E3551E719CE94538D901FDBD1F8F9920B3F0'
    $taskSignature = Get-AuthenticodeSignature -LiteralPath $taskInnoSetup
    if ($taskSignature.Status -ne 'Valid' -or $taskSignature.SignerCertificate.Subject -notmatch 'Pyrsys B.V.') { throw 'Installer compiler signature verification failed.' }
    $taskInnoRoot = Join-Path $taskTools 'InnoSetup'
    $taskInstall = Start-Process -FilePath $taskInnoSetup -ArgumentList @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/CURRENTUSER',('/DIR="'+$taskInnoRoot+'"')) -WindowStyle Hidden -PassThru -Wait
    if ($taskInstall.ExitCode -ne 0) { throw 'Installer compiler could not start.' }
    & (Join-Path $taskInnoRoot 'ISCC.exe') /Qp ('/DPayloadDir='+(Join-Path $taskPayload 'Sunny Calendar Demo')) ('/DReleaseDir='+$taskOutput) ('/DAppVersion='+$taskVersion) desktop/installer.iss
    if ($LASTEXITCODE -ne 0) { throw 'Installer compilation failed.' }
    $taskSmoke = Join-Path $taskTools 'smoke-install'
    $taskArgs = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/NOCLOSEAPPLICATIONS','/TASKS=""',('/DIR="'+$taskSmoke+'"'))
    $taskInstall = Start-Process -FilePath (Join-Path $taskOutput 'Sunny-Calendar-Setup.exe') -ArgumentList $taskArgs -WindowStyle Hidden -PassThru -Wait
    if ($taskInstall.ExitCode -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $taskSmoke 'Sunny Calendar Demo.exe'))) { throw 'Installer smoke test failed.' }
    if (Test-Path -LiteralPath (Join-Path $taskSmoke 'local-data')) { throw 'Release must not contain saved calendar data.' }
    New-Item -ItemType Directory -Path (Join-Path $taskSmoke 'local-data') | Out-Null
    Set-Content -LiteralPath (Join-Path $taskSmoke 'local-data/keep-test.txt') -Value 'Fictional test note'
    $taskUninstall = Start-Process -FilePath (Join-Path $taskSmoke 'unins000.exe') -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -WindowStyle Hidden -PassThru -Wait
    if ($taskUninstall.ExitCode -ne 0 -or (Test-Path -LiteralPath (Join-Path $taskSmoke 'Sunny Calendar Demo.exe')) -or -not (Test-Path -LiteralPath (Join-Path $taskSmoke 'local-data/keep-test.txt'))) { throw 'Uninstall data-preservation test failed.' }
    & $taskPython scripts/package-release.py --output $taskOutput --source
    if ($LASTEXITCODE -ne 0) { throw 'Release checksum generation failed.' }
} finally { Pop-Location }
