# Windows installer

The installer contains only the clean demo runtime and fictional samples. It installs for the current Windows user without administrator access. It adds a Start menu entry and a checked-by-default desktop shortcut. It does not add startup entries, change the firewall, change VPN connections or enable team syncing. If WebView2 is missing, setup runs Microsoft's bundled bootstrapper, which needs internet access. Its Microsoft signature is verified during packaging.

Saved notes and pictures are created in `local-data` inside the installed app folder. The installer never includes this folder. Upgrades preserve it and uninstall leaves it in place. Export a backup before updating.

## Build

1. Build the frontend and Windows wrapper.
2. Create the reviewed portable ZIP, excluding all saved data.
3. Extract that ZIP into a temporary payload folder.
4. Put Microsoft's official `MicrosoftEdgeWebview2Setup.exe` bootstrapper beside the payload folder, then compile `installer.iss` using Inno Setup 7.1.1. Pass `PayloadDir`, `ReleaseDir` and `AppVersion` with `/D` options.
5. Verify the installer on a separate test folder. Check the payload and that uninstall keeps a test data file.

The executable is unsigned. Windows or a company policy may block an unrecognized app. Never instruct users to turn off their security tools. Download releases only from this project's GitHub page. The app requires Windows 10/11 x64 and Microsoft Edge WebView2.
