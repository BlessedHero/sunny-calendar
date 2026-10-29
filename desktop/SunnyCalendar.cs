using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net.Http;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

// A local Windows window for the calendar. No calendar upload or Google access.
internal static class Program
{
    [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
    internal static extern int SetCurrentProcessExplicitAppUserModelID(string id);
    [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr window);
    [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr window, int command);

    [STAThread]
    private static void Main()
    {
        SetCurrentProcessExplicitAppUserModelID("Sunny.Calendar.CleanTest");
        bool first;
        using (var instance = new Mutex(true, @"Local\Sunny.Calendar.CleanTest.Window", out first))
        {
            if (!first)
            {
                foreach (var other in Process.GetProcessesByName(Process.GetCurrentProcess().ProcessName))
                {
                    if (other.Id == Process.GetCurrentProcess().Id || other.MainWindowHandle == IntPtr.Zero) continue;
                    ShowWindow(other.MainWindowHandle, 9);
                    SetForegroundWindow(other.MainWindowHandle);
                    break;
                }
                return;
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new CalendarWindow());
        }
    }
}

internal sealed class CalendarWindow : Form
{
    private const string CalendarUrl = "http://127.0.0.1:4176/";
    private readonly string root = AppDomain.CurrentDomain.BaseDirectory;
    private readonly WebView2 web = new WebView2();
    private readonly Label loading = new Label();
    private bool checkingClose, allowClose, updating;

    internal CalendarWindow()
    {
        Text = "Sunny Calendar - Demo";
        Icon = new Icon(Path.Combine(root, "calendar-icon.ico"));
        StartPosition = FormStartPosition.CenterScreen;
        Size = new Size(1500, 920);
        MinimumSize = new Size(980, 650);
        AutoScaleMode = AutoScaleMode.Dpi;
        loading.Text = "Opening your calendar...";
        loading.TextAlign = ContentAlignment.MiddleCenter;
        loading.Dock = DockStyle.Fill;
        loading.Font = new Font("Segoe UI", 14);
        loading.BackColor = Color.FromArgb(247, 249, 252);
        web.Dock = DockStyle.Fill;
        web.Visible = true;
        Controls.Add(web);
        Controls.Add(loading);
        Shown += async (sender, args) => await OpenCalendar();
        FormClosing += ConfirmSavedBeforeClosing;
    }

    private async Task<bool> IsServerReady()
    {
        try
        {
            using (var client = new HttpClient(new HttpClientHandler { UseProxy = false }))
            {
                client.Timeout = TimeSpan.FromSeconds(1);
                string status = await client.GetStringAsync(CalendarUrl + "local-api/status");
                return status.Contains("\"Sunny Calendar\"") && status.Contains("\"local-file\"") && status.Contains("\"clean-test\"");
            }
        }
        catch { return false; }
    }

    private async Task OpenCalendar()
    {
        try
        {
            if (!await IsServerReady())
            {
                string python = Path.Combine(root, "runtime", "pythonw.exe");
                if (!File.Exists(python)) throw new FileNotFoundException("The bundled runtime is missing. Extract the whole test ZIP again.");
                Process.Start(new ProcessStartInfo(python, "\"" + Path.Combine(root, "start-calendar.py") + "\" --no-open")
                { UseShellExecute = false, CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden, WorkingDirectory = root });
                bool ready = false;
                for (int attempt = 0; attempt < 40 && !IsDisposed; attempt++)
                {
                    if (await IsServerReady()) { ready = true; break; }
                    await Task.Delay(250);
                }
                if (!ready) throw new IOException("The calendar helper could not start. Another app may be using its local address. Your saved notes are still safe.");
            }
            if (IsDisposed) return;
            var environment = await CoreWebView2Environment.CreateAsync(null, Path.Combine(root, "local-data", "desktop-browser"));
            await web.EnsureCoreWebView2Async(environment);
            web.CoreWebView2.Settings.IsStatusBarEnabled = false;
            web.CoreWebView2.NavigationStarting += (sender, args) =>
            {
                Uri destination;
                if (!Uri.TryCreate(args.Uri, UriKind.Absolute, out destination) || destination.Scheme != "http" ||
                    destination.Host != "127.0.0.1" || destination.Port != 4176) args.Cancel = true;
            };
            web.CoreWebView2.WebMessageReceived += async (sender, args) =>
            {
                if (args.Source != CalendarUrl || updating) return;
                string message;
                try { message = args.TryGetWebMessageAsString(); } catch { return; }
                if (message != "sunny-update-now") return;
                updating = true;
                try
                {
                    string unsaved = await web.CoreWebView2.ExecuteScriptAsync("(() => { const s=document.querySelector('.save-bar'); return !s || /Saving|Could not save|Opening/.test(s.dataset.saveStatus || s.innerText); })()");
                    if (unsaved != "false") throw new IOException("Save notes first");
                    using (var client = new HttpClient(new HttpClientHandler { UseProxy = false }))
                    {
                        client.Timeout = TimeSpan.FromSeconds(20);
                        client.DefaultRequestHeaders.Add("Origin", CalendarUrl.TrimEnd('/'));
                        string body = "{\"clientPid\":" + Process.GetCurrentProcess().Id + "}";
                        var response = await client.PostAsync(CalendarUrl + "local-api/updates/launch", new StringContent(body, System.Text.Encoding.UTF8, "application/json"));
                        response.EnsureSuccessStatusCode();
                    }
                    allowClose = true;
                    Close();
                }
                catch { updating = false; if (!IsDisposed) web.CoreWebView2.PostWebMessageAsString("sunny-update-failed"); }
            };
            web.CoreWebView2.NewWindowRequested += (sender, args) => { args.Handled = true; };
            web.CoreWebView2.NavigationCompleted += (sender, args) =>
            {
                if (!args.IsSuccess) { loading.Text = "The calendar could not open. Close this window and try again. Your saved notes are safe."; return; }
                loading.Visible = false;
                web.Visible = true;
                web.BringToFront();
                web.Bounds = ClientRectangle;
                web.PerformLayout();
                web.Focus();
            };
            web.CoreWebView2.Navigate(CalendarUrl);
        }
        catch (Exception error)
        {
            loading.Text = "Sunny Calendar could not open.\nYour saved notes are safe.\n\n" + error.Message;
        }
    }

    private async void ConfirmSavedBeforeClosing(object sender, FormClosingEventArgs args)
    {
        if (allowClose || web.CoreWebView2 == null) return;
        args.Cancel = true;
        if (checkingClose) return;
        checkingClose = true;
        bool unsaved = true;
        try
        {
            // Read the app's visible save status; do not close silently over a failed save.
            string result = await web.CoreWebView2.ExecuteScriptAsync(
                "(() => { const s=document.querySelector('.save-bar'); return !s || /Saving|Could not save|Opening/.test(s.dataset.saveStatus || s.innerText); })()");
            unsaved = result == "true";
        }
        catch { }
        if (!unsaved || MessageBox.Show(this,
            "Some notes may still need saving. Choose Cancel to keep this window open and use Export backup.\n\nClose anyway?",
            "Sunny Calendar", MessageBoxButtons.OKCancel, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) == DialogResult.OK)
        {
            if (!unsaved)
            {
                // Exit the local helper too, so the next open loads updated files.
                try
                {
                    using (var client = new HttpClient(new HttpClientHandler { UseProxy = false }))
                    {
                        client.Timeout = TimeSpan.FromSeconds(2);
                        client.DefaultRequestHeaders.Add("Origin", CalendarUrl.TrimEnd('/'));
                        await client.PostAsync(CalendarUrl + "local-api/updates/shutdown", new StringContent("{}", System.Text.Encoding.UTF8, "application/json"));
                    }
                }
                catch { }
            }
            allowClose = true;
            Close();
        }
        checkingClose = false;
    }
}
