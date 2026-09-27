# AirMouse

[繁體中文版](README.zh.md)

Turn your iPhone into a touchpad, mouse, and keyboard for your Windows PC using
Safari. No iOS app required — just connect over the browser on the same Wi-Fi
network.

## Installation

There are two ways to install; pick one:

### Option A: Download AirMouse.exe (recommended, no Python needed)

Download `AirMouse.exe` from [Releases](../../releases), put it in whatever
folder you like, and double-click to run — no Python or anything else
required.

**The first time you run it, Windows Firewall will prompt you** ("Windows
Security" asking whether to allow Python/AirMouse network access) — click
"Allow". If you later want it to auto-start at boot with administrator
privileges (needed to control elevated windows like Task Manager), put
`setup_autostart_exe.ps1` in the same folder and run it once **as
administrator**:

```powershell
powershell -ExecutionPolicy Bypass -File setup_autostart_exe.ps1
```

This is a one-time setup. After that, AirMouse will automatically start as
administrator in the background on every boot, and restart itself if it's
ever stopped — no manual steps needed.

> ⚠️ **Your antivirus may flag a false positive**: `AirMouse.exe` isn't
> signed with a commercial code-signing certificate (those cost money), and
> its behavior — listening on the network, simulating mouse/keyboard input —
> resembles some remote-access malware. Some antivirus tools / Windows
> Defender may misidentify it as a result. This is a false positive — if
> you're not comfortable with that, review the source in
> [`server.py`](server.py) and [`winput.py`](winput.py), or use Option B to
> build it yourself from source so you know exactly what code is running.

### Option B: Run from source (for developers, or if you want to review the code first)

1. Make sure you have Python 3.12 or later installed (if not:
   `winget install Python.Python.3.12`)
2. Open this folder in PowerShell and run:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```
   This creates a virtual environment, installs dependencies, and (if run as
   administrator) adds a firewall rule scoped to the **Private network**
   profile only.
3. If you want it to auto-start at boot, the installer will ask if you want
   to set up a Task Scheduler entry.

Want to build `AirMouse.exe` yourself from source? After setting up the venv,
run `powershell -ExecutionPolicy Bypass -File build_exe.ps1` — the executable
will be at `dist\AirMouse.exe`.

## Starting AirMouse

**Option A (exe)**: double-click `AirMouse.exe`.

**Option B (source)**: double-click `start.bat`, or run in PowerShell:

```powershell
.\.venv\Scripts\python.exe server.py
```

Either way, a welcome window appears showing the URL, an ASCII QR code, and it
also automatically pops up a larger graphical QR code (handy for photographing
or scanning directly), with a URL that looks like:

```
https://192.168.1.23:8765/?token=xxxxxxxx
```

Scan the QR code with **Safari** on your iPhone (not Chrome or another
browser — "Add to Home Screen" only works reliably in Safari), or type the URL
manually.

**On first connection you'll see a "This Connection Is Not Private" warning**
— this is expected, because the certificate is self-signed (there's no public
domain, so there's no way to get a certificate a browser trusts by default).
Tap "Show Details" → "Visit this website" once, and your phone won't ask
again.

**Once your phone connects successfully, the welcome window automatically
minimizes to the Windows system tray** so it's out of your way. To see the QR
code again later, or to fully quit AirMouse, see "Tray Icon" below. Before any
phone has connected, this window stays open — if you accidentally click the X
to close it, the server stops (this is intentional, since nothing is
connected yet anyway).

### Tray Icon

AirMouse adds an icon to the Windows system tray (bottom-right, near the
clock) as soon as it starts — if you don't see it, it may be hidden under the
"Show hidden icons" arrow (^), which is typical for a program's first
appearance on Windows.

- **Click (or double-click)**: pop the QR code window back up (useful if your
  phone lost the QR code, or you want to connect a second phone)
- **Right-click**: opens a menu with "Show QR Code" and "Quit AirMouse" — use
  "Quit" to actually stop the server; don't just End Task it in Task Manager
  (see Known Limitations below)

### Add to Home Screen (use it like an app)

After opening the page in Safari, tap the Share button → "Add to Home
Screen". You can then launch it from your home screen like any other app,
without typing the URL again.

## Usage

- **One-finger move on the touchpad** = move the cursor (slow = precise,
  fast = travels further)
- **One-finger tap** = left click
- **Two-finger tap** = right click
- **Two-finger drag** = scroll (with inertia)
- **Tap, then immediately press and drag** = drag (equivalent to holding down
  left-click and dragging)
- Bottom buttons: left click, right click, ⌨️ keyboard mode, 🎵 media
  controls
- Keyboard mode has a text field that supports Chinese input methods, plus
  quick-access buttons for Esc, Tab, arrow keys, Ctrl+C/V/Z, Alt+Tab, Win,
  etc.
- Gear icon ⚙️ (top right) = settings (sensitivity, scroll speed, reverse
  scroll)
- The dot at the top shows connection status; it auto-reconnects if
  disconnected

## Security Design

- On first launch, a random token is generated in `config.json` — the URL
  must include the correct token to connect (verified on both the WebSocket
  and the web page, using `secrets.compare_digest` to prevent timing
  attacks)
- **Everything is encrypted over HTTPS/WSS**: on first launch, a self-signed
  certificate is automatically generated in `cert.pem`/`key.pem`, and all
  traffic (including every keystroke and mouse movement) is encrypted with
  TLS rather than sent in plaintext over Wi-Fi. This matters because without
  encryption, anyone else on the same Wi-Fi network (especially
  WPA2-Personal) who knows the password could theoretically intercept your
  keystrokes
- The server listens on `0.0.0.0`, but the firewall rule only opens it to the
  **Private** network profile — it's never exposed to the public internet
- Your phone's browser stores the token in `localStorage`, so once added to
  the home screen you won't need to re-enter it
- This tool is meant for use on a home network you trust — don't port-forward
  it to the internet
- `config.json`, `cert.pem`, and `key.pem` are already in `.gitignore` so
  they won't get committed by accident — if you fork this project, don't
  manually add these files back to git; they're private data specific to
  your own machine

## Known Limitations

- The server runs with normal user privileges. To control a program running
  with **administrator privileges** (e.g. certain elevated windows), you need
  to run the AirMouse server as administrator too (this is a Windows UIPI
  restriction — a lower-privilege process can't send input to a
  higher-privilege window)
- It cannot control the Windows **login screen** or **UAC prompts** (these
  run on a separate Secure Desktop that input-simulation APIs can't reach)
- Your phone and PC must be on **the same Wi-Fi network**
- Only tested on iPhone Safari; touch gestures and "Add to Home Screen"
  behavior may differ on other browsers (especially Android Chrome)
- To stop AirMouse, use "Quit" from the tray icon menu. Ending the process
  directly in Task Manager also works, but won't clean up the tray icon
  (it lingers until you hover over it) — using the tray menu's "Quit" is
  cleaner

## File Structure

```
phonemouse/
  server.py          aiohttp app, WebSocket handler, token verification, tray icon logic
  winput.py          SendInput wrapper (mouse_move, click, scroll, type_text, key_combo, media)
  traymenu.py        System tray icon written directly with ctypes (Shell_NotifyIcon), no pystray/Pillow
  static/index.html  Phone UI
  static/manifest.json + icon-*.png   Used for Add to Home Screen
  static/tray.ico    Tray icon file
  config.json        Port / token / sensitivity settings (auto-generated on first run)
  cert.pem / key.pem Self-signed TLS certificate (auto-generated on first run, gitignored)
  requirements.txt
  install.ps1        (Option B) creates venv, installs dependencies, adds firewall rule
  start.bat          (Option B) double-click to start, shows QR code then runs in background
  build_exe.ps1      (Option B) builds dist\AirMouse.exe with PyInstaller
  AirMouse.spec      PyInstaller build config
  setup_autostart_exe.ps1  (Option A) sets up AirMouse.exe to auto-start as administrator at boot
```

## Troubleshooting

- **Phone can't open the page**: confirm the phone and PC are on the same
  Wi-Fi network, and that the firewall rule was added successfully (check
  "Windows Defender Firewall" → "Advanced Settings" for an `AirMouse` rule).
- **Page loads but keys/movement don't respond**: usually a failed WebSocket
  token check — try rescanning the QR code, or clear Safari's site data and
  reopen the page.
- **Chinese characters won't type / show as garbage**: this uses
  `KEYEVENTF_UNICODE` to send characters directly, which should work in any
  application (including Notepad and browsers); some older programs or games
  that don't support Unicode input may not work — use a physical keyboard for
  those.
- **Home screen icon stops working after an update**: if you added the app
  to your home screen before HTTPS was added, the old icon points to a now-
  invalid `http://` URL. Delete the old icon, open the new `https://` URL in
  Safari (or rescan the QR code), and add it to the home screen again.
- **Can't find the tray icon**: Windows typically hides a program's icon the
  first time it appears, under the "Show hidden icons" arrow (^) at the
  bottom right. Click the arrow to find it; to keep it always visible, drag
  AirMouse out of that menu, or go to Windows Settings → Personalization →
  Taskbar → "Select which icons appear on the taskbar" and enable it
  manually.

## License

[MIT](LICENSE)
