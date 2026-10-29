# Clean Windows wrapper

Build with `desktop/build.ps1` on Windows with .NET Framework and the WebView2 SDK assemblies beside the executable. Their license notices are included.

The executable starts `runtime/pythonw.exe` and the separate port 4176 helper. Its single-instance identity is Sunny.Calendar.CleanTest. It never points to the working calendar or the user's Codex runtime folder.
