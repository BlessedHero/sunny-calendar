# Demo verification — 2026-10-29

## Windows installer 0.2.1

- Built Sunny-Calendar-Setup.exe with Inno Setup 7.1.1. Verified the compiler download's valid vendor signature and retained its license. The vendor's included license permits commercial applications; a paid license is requested, not mandatory.
- Verified Microsoft's WebView2 bootstrapper has a valid Microsoft signature before bundling. On this PC, setup correctly detected the installed WebView2 runtime and skipped that prerequisite. The missing-runtime download path has not been tested by removing Windows components.
- Installed the final package into a separate test folder, without shortcuts or automatic launch. Setup returned 0. The executable, bundled Python and static app files were present; the first installation contained no saved calendar data.
- Reinstalled over a fictional local-data test file; the file remained. Uninstalled the package; the application files were removed and the local-data test file remained. No working calendar files were changed.
- Setup uses a per-user folder, current-user shortcuts and no administrator elevation. It starts at the Install page, selecting English or Korean from Windows. No startup entries, firewall changes or VPN actions are included. An existing Sunny Calendar desktop shortcut is preserved.
- This is an unsigned early release. GitHub publishing requires a browser sign-in and is not confirmed by these local checks.

- Built the frontend and separate Windows executable.
- The native app cold-started its bundled Python helper on port 4176. It does not use Codex's Python installation.
- New data files receive eight fictional SAMPLE tasks and two fictional memos, using ABC Company and XYZ Company. Examples are dated in the first-open month.
- Sample initialization runs once. Deleting a sample does not recreate it on reload. Existing user records are never overwritten by sample initialization.
- An isolated test on port 4177 verified multiline task saving, checked state and deletion persistence with the bundled Python runtime.
- The working calendar on port 4173 remained unchanged.
- Scanned source and built text for original business identifiers and employee-name examples; none were found.
- Source and runtime ZIPs exclude databases, browser profiles, backups, screenshots and local desktop settings. Runtime licenses are included.
- Team Sync and cloud accounts are not implemented or enabled. No GitHub upload or public release has been performed.


## 2026-10-29: team draft controls and sidebar network search
- Both production builds pass.
- Separate fixture server on 4177: first ++ asks for setup; Cancel adds nothing; enabling once survives reload; the next ++ opens the task directly. Settings disables the mode without deleting existing drafts, and the next ++ asks again.
- Team metadata remains aligned after personal-task deletion and Undo; completion changes keep the team outline. Backup JSON retains teamLayers. Adding a team task to 19 existing tasks produces 20 total with four month previews and both add buttons disabled.
- All 35 tested date cells keep their cards and add buttons inside the cell; ++ and + have 9 px separation.
- Top search reveals and focuses the left search. Two-backslash addresses show an explicit Open network computer action instead of zero note matches. Enter opens File Explorer through the existing local API. A real office computer was reachable and displayed five shares. No Windows sharing settings or credentials were changed.
- Small-window search/settings icons remain visible. Korean labels verified in the working browser.
- Working calendar comparison: 21 document bodies exactly match the earlier snapshot. One day has one newly added empty personal card; its original three task layers and completion flags are unchanged. The blank card was preserved. No real records were tagged as team tasks.
- Coworker sync is NOT implemented. The app clearly labels team entries as local drafts and connection status as Not connected.

## 0.3.2 release checks — 2026-10-30

- Vite build, four Sites worker checks, three task color checks and nineteen Python update/app-link checks pass.
- Real Windows app-picker selection and per-computer POS path persistence verified; optional button hiding and missing-app setup verified.
- Native 0.3.1 to 0.3.2 update: verified installer, backup, saved-window closure, interactive Install/Finish and automatic reopen passed. Seven fictional database records, including a pasted image, retained the same bodies and revisions.
- Public source uses empty imported seeds and project-only Git author identity. User data and per-computer settings are excluded.
- Cancelling the normal installer reopened the original version; all seven test records and revisions remained unchanged.
