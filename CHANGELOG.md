# Change history

## 0.3.1 — 2026-10-29

- Balanced each day header: ++ at the far left, the date centered, and + at the far right.
- Added the Update now window with a verified installer download and a local backup. Update closes the saved Windows app, opens the normal installer and reopens the calendar afterward. Cancelled installations reopen the original app.
- Fixed first upgrades blocked by the older background helper. The installer requires the calendar window to close through its app mutex before clearing its own older runtime.

## 0.3.0 — 2026-10-29

- Added a glossy blue update button with an automatic release check when the app opens, honest offline status, a local backup before opening the official installer, and English/Korean guidance.
- Kept installation manual as requested. The app does not silently install software or notify users while closed.
- Centered date numbers across every day header while keeping add controls on the right.

- Enlarged weekday headings by 50 percent and made weekday names and date numbers bold.

- Shared task cards use a green left stripe in every view while keeping their pastel backgrounds.

- Halved the visible ++ controls, reduced task checkboxes by one-third, and made unfinished red task text bold.

- Team tasks and ++ controls now default to green. Completion turns task text and outlines black; reopening restores the saved color.
- Added manual whole-task colors for unfinished team tasks, preserved through deletion, Undo, save and backup.
- Replaced the team-task badge with grey Team not connected. A green neon Team connected style is reserved for a real future sync connection; local team mode is not a network connection.
- Updated English/Korean color guidance. Personal tasks keep red/black completion colors.

## 0.2.2 — 2026-10-29

- Replaced the public history with a project-only author identity.
- Added a release check that rejects personal author details.
- Kept the calendar features and local storage behavior unchanged.

## 0.2.1 — 2026-10-29

- Added a per-user Windows installer with English/Korean setup and desktop and Start menu shortcuts.
- Bundled Microsoft's WebView2 bootstrapper for PCs missing the display runtime.
- Added an Install button and simple coworker instructions.
- Kept saved data out of packages; uninstall leaves saved notes in place.

## 0.2.0 — 2026-10-29

- Raised red ++ controls and bold outlines for local team drafts.
- One-time enable flow, remembered mode and Settings off switch.
- Explicit Not connected status; live coworker sync remains future work.
- Top search focuses the sidebar and handles Windows network computer addresses on Enter.
- Keep search/settings buttons visible in narrower windows.


## 0.1.0 — 2026-10-29

- Created a separate clean coworker demo edition.
- Removed all real company entries and imports. Added only editable, deletable ABC/XYZ SAMPLE tasks and memos.
- Kept the existing editing, language, shortcut and filename-search features.
- Isolated saved data, browser storage, native app identity and loopback port from the working calendar.
