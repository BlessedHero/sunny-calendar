#ifndef AppVersion
  #define AppVersion "0.2.1"
#endif
#ifndef PayloadDir
  #define PayloadDir "..\..\..\work\installer-payload\Sunny Calendar Demo"
#endif
#ifndef ReleaseDir
  #define ReleaseDir "..\..\.."
#endif

[Setup]
AppId={{D9FEE12B-6D81-4C62-A0AA-A546F241C7F8}
AppName=Sunny Calendar
AppVersion={#AppVersion}
AppPublisher=Sunny Calendar contributors
AppPublisherURL=https://github.com/BlessedHero/sunny-calendar
AppSupportURL=https://github.com/BlessedHero/sunny-calendar/issues
AppUpdatesURL=https://github.com/BlessedHero/sunny-calendar/releases/latest
DefaultDirName={localappdata}\Programs\SunnyCalendarDemo
DefaultGroupName=Sunny Calendar
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableWelcomePage=yes
DisableDirPage=yes
DisableProgramGroupPage=yes
DisableReadyPage=no
AllowNoIcons=yes
WizardStyle=modern
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
Compression=lzma2/normal
SolidCompression=yes
OutputDir={#ReleaseDir}
OutputBaseFilename=Sunny-Calendar-Setup
SetupIconFile=..\calendar-icon.ico
UninstallDisplayIcon={app}\calendar-icon.ico
CloseApplications=yes
RestartApplications=no
AppMutex=Local\Sunny.Calendar.CleanTest.Window
UninstallDisplayName=Sunny Calendar

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#PayloadDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Excludes: "local-data\*,__pycache__\*"
Source: "{#PayloadDir}\..\MicrosoftEdgeWebview2Setup.exe"; Flags: dontcopy

[Icons]
Name: "{group}\Sunny Calendar"; Filename: "{app}\Sunny Calendar Demo.exe"; WorkingDir: "{app}"; IconFilename: "{app}\calendar-icon.ico"; AppUserModelID: "Sunny.Calendar.CleanTest"
Name: "{autodesktop}\Sunny Calendar"; Filename: "{app}\Sunny Calendar Demo.exe"; WorkingDir: "{app}"; IconFilename: "{app}\calendar-icon.ico"; Tasks: desktopicon; AppUserModelID: "Sunny.Calendar.CleanTest"; Check: not FileExists(ExpandConstant('{autodesktop}\Sunny Calendar.lnk'))

[Run]
Filename: "{app}\Sunny Calendar Demo.exe"; Description: "{cm:LaunchProgram,Sunny Calendar}"; Flags: nowait postinstall skipifsilent

; There is deliberately no UninstallDelete rule. Notes and pictures created in
; local-data are not installer files and are left in place on uninstall.

[Code]
function ShouldSkipPage(PageID: Integer): Boolean;
begin
  { The desktop shortcut is enabled by default; go straight to Install. }
  Result := PageID = wpSelectTasks;
end;

function HasWebView2: Boolean;
var
  Version: String;
  Key: String;
begin
  Key := 'Software\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}';
  Result := (RegQueryStringValue(HKLM32, Key, 'pv', Version) or
             RegQueryStringValue(HKCU32, Key, 'pv', Version) or
             RegQueryStringValue(HKCU64, Key, 'pv', Version)) and
             (Version <> '') and (Version <> '0.0.0.0');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  if HasWebView2 then begin
    Log('Microsoft WebView2 is already installed.');
    exit;
  end;
  ExtractTemporaryFile('MicrosoftEdgeWebview2Setup.exe');
  if not Exec(ExpandConstant('{tmp}\MicrosoftEdgeWebview2Setup.exe'), '/silent /install', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then begin
    Result := CustomMessage('WebViewInstallFailed');
    exit;
  end;
  if ResultCode = 3010 then NeedsRestart := True;
  if not HasWebView2 then Result := CustomMessage('WebViewInstallFailed');
end;

[CustomMessages]
english.WebViewInstallFailed=Microsoft WebView2 could not be installed. Check your internet connection or ask your IT team, then run Sunny Calendar Setup again. No calendar notes were changed.
korean.WebViewInstallFailed=Microsoft WebView2를 설치하지 못했습니다. 인터넷 연결을 확인하거나 전산 담당자에게 문의한 뒤 써니 캘린더 설치를 다시 실행하세요. 캘린더 메모는 변경되지 않았습니다.
