# Sunny Calendar · 써니전자 캘린더

[![Install for Windows / 윈도우 설치](public/install-windows.svg)](https://github.com/BlessedHero/sunny-calendar/releases/latest/download/Sunny-Calendar-Setup.exe)

**For coworkers:** click the blue button, open **Sunny-Calendar-Setup.exe**, then click **Install**. Use the Sunny Calendar desktop shortcut next time. No GitHub account, Codex, Node.js or Python is needed.

**동료 설치 안내:** 파란 설치 버튼을 누르고, 다운로드한 **Sunny-Calendar-Setup.exe**를 연 뒤 **설치**를 누르세요. 다음부터 바탕 화면의 **Sunny Calendar** 아이콘으로 열 수 있습니다. GitHub 계정이나 코딩 프로그램은 필요하지 않습니다.

Windows 10/11 x64. Setup installs for the current Windows user and normally needs no administrator password. It adds desktop and Start menu shortcuts. If Microsoft WebView2 is missing, setup uses Microsoft's bootstrapper and needs internet access. A company policy can still block installation.

This is an early test release. The app is unsigned, so Windows may warn about an unknown publisher. Do not turn off your security software. Ask your IT team if company policy blocks it.

**Private data stays on each computer. Team drafts do not sync yet.** Only fictional samples are included. Installing does not copy any real work records or connect a shared calendar.

**개인 데이터는 각 컴퓨터에 저장됩니다. 팀 공유 초안은 아직 동기화되지 않습니다.** 가상 예제만 포함되어 있으며 실제 업무 기록은 들어 있지 않습니다.

---

This separate Windows demo contains only fictional SAMPLE entries for ABC Company and XYZ Company, plus sample tasks and memos. You can edit or delete every example. Korean public holidays remain as calendar reference dates. No company records, old screenshots, workbook data, browser profiles, databases or backups are included.

## Updating after this version is installed

Sunny Calendar checks this project's public GitHub release information when the app opens. It does not upload your notes or pictures. Reloads within 15 minutes may reuse the last successful check. There are no update alerts while the app is closed.

The glossy blue button shows **Update available · v…** when a newer installer is ready, or **Up to date · v…** after a successful check. If the internet check fails, it offers **Check updates** and explains that the calendar still works.

Clicking an available update waits for saved notes, downloads and verifies this project's official installer, and makes a local backup in the app's `local-data/backups` folder. The **Sunny Calendar — Update now** window offers **Cancel** and **Update**. In the installed Windows app, Update closes the saved calendar, opens the normal Windows installer and reopens the calendar when that installer ends. Windows may still ask you to click **Install**. If you cancel installation, the original calendar reopens. The backup JSON can be used with **Restore backup**. The installer is not silent. Browser previews and working test copies do not replace the installed app automatically.

동료용 앱을 열면 GitHub의 공개 버전 정보만 확인하며, 메모나 그림은 업로드하지 않습니다. 파란 버튼에 **새 버전 v… 업데이트 가능** 또는 **최신 버전 · v…**이 표시됩니다. 새 설치 파일을 검증하고 백업을 저장한 뒤 **써니전자 캘린더 — 지금 업데이트** 창이 열립니다. 설치된 Windows 앱에서 **업데이트**를 누르면 저장된 캘린더를 닫고 설치 화면을 연 뒤 캘린더를 다시 엽니다. Windows 화면에서 **설치**를 눌러야 할 수 있습니다. 설치를 취소하면 기존 캘린더가 다시 열립니다.

## Optional portable ZIP

1. Right-click the downloaded ZIP and choose Extract All.
2. Open the extracted folder.
3. Double-click **Sunny Calendar Demo.exe**.
4. Use **Eng / Kor** to choose English or Korean.

Python is bundled. Codex and a separate Python installation are not required. The window needs the Microsoft Edge WebView2 runtime, normally present on current Windows PCs. If it is missing, get it from Microsoft's official page: https://developer.microsoft.com/microsoft-edge/webview2/.

Keep all extracted files together when using the optional portable ZIP. The Install button above uses the simpler setup program. Neither version adds a startup entry.

This edition uses loopback port 4176, its own Windows identity and its own local-data folder. The working calendar on port 4173 stays separate. Each coworker has their own local notes. Sharing this app does not enable shared calendars or syncing.

## Included features

- Month view, Korean holidays, ISO week numbers, sidebar toggles and page turns.
- Direct multiline task editing, four preview cards, full-day view for extra tasks, font sizes, completion checkboxes, confirmed deletion and Undo.
- Editable sample monthly/permanent memos, screenshot paste/resizing, tables and note backup/restore.
- English/Korean labels, help and hover tips.
- Obsidian, Sunny POS and SoftEther VPN launch buttons where those apps are installed. Users handle POS sign-in and VPN connections. POS uses the Sunny office installation path and is optional on other PCs.
- Three empty shortcut slots and filename search. Users choose their own local/shared folders. A network address such as \\COMPUTER opens through File Explorer using existing Windows access.

## 한국어 시작 안내

ABC Company와 XYZ Company의 가상 예제가 들어 있는 별도 데모 캘린더입니다. 예제 할 일과 메모는 모두 수정하거나 삭제할 수 있습니다. ZIP 파일을 압축 해제한 뒤 **Sunny Calendar Demo.exe**를 여세요. 기존 업무용 캘린더는 변경되지 않습니다. 한국 공휴일은 기본 참고 정보로 표시됩니다. 이 앱을 나누어 사용해도 서로의 일정이 자동으로 공유되지는 않습니다.

## Source development

For this project, set the local Git author name to **Sunny Calendar contributors** and email to **sunny-calendar@local.invalid**. Run `python scripts/check-release-privacy.py` before publishing. The release packager checks the public history automatically. Keep personal recovery branches private.

Install a supported Node.js release, then run `npm ci` and `npm run build` in this folder. The Python helper uses only the standard library. The Windows wrapper is built with `desktop/build.ps1` and the WebView2 assemblies.

Never commit local-data, browser profiles, screenshots, personal backups, compiled files or runtime folders. Before a public release, review dependencies, third-party licenses, office-specific integrations and branding. The project code has an MIT license; third-party files retain their own licenses.

Keep the public project limited to clean source and release packages. Never upload local-data or personal backups. The installer build is described in desktop/INSTALL.md.

Sample entries are created only once, in the month when a new user first opens the app. Deleted samples stay deleted. Team Sync is a future optional feature; this package is local-only.


## Team drafts and network search
Each date has a raised green **++** beside the personal **+**. The first ++ asks to enable team draft mode. The setting stays on until turned off in Settings. Team tasks start green with a bold outline. Checking a task turns it black; unchecking restores its previous color. The color buttons can change an unfinished team task's whole text and outline. Personal tasks keep red/black completion colors. Turning the mode off keeps existing tasks. These tasks still save only on this computer; coworker syncing is **not connected**. The grey **Team not connected** badge reflects that state. A green glowing **Team connected** badge is reserved for a future real sync connection; enabling the local mode does not connect coworkers.

Click the top magnifying glass to open and focus the left search. Ordinary words find calendar notes. Type two backslashes followed by a computer name and press Enter, or click Open network computer, to open that computer in Windows File Explorer. Windows uses the access you already have. This does not enable shared calendar syncing. To search filenames inside a network share, add the specific shared folder through Search files > Search folders.

Setup programs are built with Inno Setup 7.1.1 by Jordan Russell and contributors. Its license is included in licenses/Inno-Setup.txt.
