# AirMouse

[Read in English](README.md)

用 iPhone 嘅 Safari 瀏覽器,將手機變成 Windows 電腦嘅觸控板、滑鼠同鍵盤。唔使裝任何
iOS app,淨係喺同一個 Wi‑Fi 內網用瀏覽器連接就得。

## 安裝

有兩種方式,揀一種就得:

### 方式 A:下載 AirMouse.exe(推薦,唔使裝 Python)

去 [Releases](../../releases) 下載 `AirMouse.exe`,放喺你想要嘅資料夾,
雙擊執行就得——完全唔使裝 Python 或者任何嘢。

**第一次雙擊會彈出 Windows 防火牆提示**(「Windows 安全性」問你准唔准
Python/AirMouse 用網絡)——撳「允許」。之後如果想設定「開機自動以管理員
身份啟動」(咁樣先控制到 Task Manager 呢啲已提升權限嘅視窗),將
`setup_autostart_exe.ps1` 放埋同一個資料夾,以**管理員身份**執行一次:

```powershell
powershell -ExecutionPolicy Bypass -File setup_autostart_exe.ps1
```

呢個係一次性設定,之後每次開機都會自動以管理員身份、喺背景默默啟動,
斷咗仲會自動重新啟動,唔使再手動做任何嘢。

> ⚠️ **防毒軟件可能會誤報**:AirMouse.exe 冇經過商業程式碼簽署(要
> 錢),而且佢嘅行為(監聽網絡、模擬滑鼠鍵盤輸入)同某啲遠端控制惡意
> 程式相似,部分防毒軟件/Windows Defender 可能會誤判。呢個係 false
> positive——如果唔放心,可以睇 [`server.py`](server.py) 同
> [`winput.py`](winput.py) 嘅原始碼,或者用方式 B 由自己部機用 Python
> 建構,確保運行嘅係你睇過嘅程式碼。

### 方式 B:用原始碼行(適合開發者,或者想睇晒程式碼先信)

1. 確保電腦有 Python 3.12 或以上版本(冇嘅話: `winget install Python.Python.3.12`)
2. 用 PowerShell 開呢個資料夾,執行:
   ```powershell
   powershell -ExecutionPolicy Bypass -File install.ps1
   ```
   會自動建立虛擬環境、安裝依賴,並(如果用管理員身份執行)加一條只限
   **Private network** 嘅防火牆規則。
3. 如果想開機自動啟動,安裝過程會問你要唔要設定 Task Scheduler。

想自己由原始碼建構出 `AirMouse.exe`?裝好 venv 之後執行
`powershell -ExecutionPolicy Bypass -File build_exe.ps1`,執行檔會喺
`dist\AirMouse.exe`。

## 啟動

**方式 A(exe)**:雙擊 `AirMouse.exe` 就得。

**方式 B(原始碼)**:雙擊 `start.bat`,或者喺 PowerShell 行:

```powershell
.\.venv\Scripts\python.exe server.py
```

兩種方式都會顯示一個歡迎畫面,印出網址、ASCII QR code,仲會自動幫你彈出
一張大嘅圖形化 QR code(方便直接影相/掃描),例如網址格式:

```
https://192.168.1.23:8765/?token=xxxxxxxx
```

用 iPhone 嘅 **Safari**(唔好用 Chrome/其他瀏覽器,加到主畫面呢個功能只有
Safari 做得穩)掃個 QR code,或者手動輸入網址開啟。

**第一次連接會見到「連線並非私人連線」嘅警告**——呢個係正常現象,因為
呢個係自簽發嘅證書(冇公開網域,冇辦法攞到瀏覽器信任嘅正式證書)。撳
「顯示詳細資料」→「前往此網頁」一次就得,之後呢部手機都唔會再問。

**手機連接成功之後,呢個歡迎視窗會自動收埋去 Windows 工作列(system
tray)**,唔會再佔住個螢幕。之後想再睇 QR code,或者想完全結束
AirMouse,睇下面「工作列圖示」一節。喺未有手機連接之前,呢個視窗係開住
嘅,如果你手多手快撳咗個 X 掣閂咗佢,server 就會停(咁做安全,因為根本
仲未有人連接緊)。

### 工作列圖示

AirMouse 一開機就會喺 Windows 工作列(右下角,時鐘附近)出現一個圖示——
如果見唔到,可能收埋咗喺「顯示隱藏的圖示」(個向上箭嘴 ^)入面,Windows
對第一次見到嘅程式通常都係咁。

- **撳一下(或雙擊)**:重新彈出 QR code 圖(手機唔見咗個 QR、或者換咗
  第二部手機想連接嘅時候用)
- **右鍵**:彈出選單,有「顯示 QR Code」同「結束 AirMouse」兩個選項——
  想真正停止 server,用呢個「結束」,唔好淨係喺 Task Manager 度亂咁
  End Task(見下面已知限制)

### 加到主畫面(當 app 用)

喺 Safari 開頁面後,撳分享按鈕 → 「加入主畫面」,之後就可以好似普通 app 咁
喺主畫面撳圖示開啟,唔使再打網址。

## 使用方法

- **單指喺觸控板移動** = 移動滑鼠游標(慢郁精準、快郁走得遠)
- **單指輕點** = 左鍵
- **雙指輕點** = 右鍵
- **雙指拖曳** = 捲動(支援慣性)
- **輕點一下之後即刻按住拖** = 拖曳(相當於撳住左鍵拖曳)
- 底部按鈕:左鍵、右鍵、⌨️ 鍵盤模式、🎵 媒體控制
- 鍵盤模式入面有一個輸入格,支援中文輸入法;仲有 Esc、Tab、方向鍵、
  Ctrl+C/V/Z、Alt+Tab、Win 等快捷鍵按鈕
- 右上角齒輪 ⚙️ = 設定(靈敏度、捲動速度、反向捲動)
- 頂部圓點顯示連線狀態,斷線會自動重新連接

## 保安設計

- 第一次啟動會喺 `config.json` 產生一個隨機 token,網址一定要帶正確 token
  先連接得到(WebSocket 同網頁都會驗,用 `secrets.compare_digest` 防
  timing attack)
- **全程用 HTTPS/WSS 加密**:第一次啟動會自動喺 `cert.pem`/`key.pem`
  產生一個自簽發證書,所有流量(包括你打嘅每一個字、滑鼠移動)都經過
  TLS 加密,唔會喺 Wi‑Fi 度以明文傳送。呢個好重要,因為冇加密嘅話,
  同一個 Wi‑Fi(尤其 WPA2-Personal)入面知道密碼嘅其他人,理論上有可能
  截取到你嘅按鍵內容
- Server 監聽 `0.0.0.0`,但防火牆規則只開放畀 **Private** 網絡設定檔,
  唔會開埠去外網
- 手機瀏覽器會將 token 存喺 `localStorage`,加到主畫面之後都唔使再手動輸入
- 呢個工具只應該喺你信任嘅家居內網使用,唔好將 port 轉發去外網
- `config.json`、`cert.pem`、`key.pem` 已經加咗入 `.gitignore`,唔會被
  誤 commit——如果你 fork 呢個 project,千祈唔好手動將呢幾個檔案加返落
  git,佢哋係你自己部機專屬嘅私密資料

## 已知限制

- Server 行喺一般使用者權限,如果要控制嘅程式係以**管理員權限**開嘅
  (例如某啲已提升權限嘅程式),就需要用管理員身份執行 AirMouse server
  先控制得到(Windows 嘅 UIPI 限制,低權限程序唔可以送輸入去高權限視窗)
- 控制唔到 Windows **登入畫面**同 **UAC 提示**(呢啲畫面运行喺獨立嘅
  Secure Desktop,一般輸入模擬 API 到唔到)
- 手機同電腦一定要連**同一個 Wi‑Fi** 先用得到
- 只喺 iPhone Safari 測試過;其他瀏覽器(尤其 Android Chrome)嘅觸控手勢
  同「加到主畫面」行為可能有出入
- 想停止 AirMouse,請用工作列圖示嘅「結束」選項;喺 Task Manager 度直接
  End Task 都得,但唔會清理工作列圖示(要滑鼠移過去先會消失),用工作列
  嘅「結束」會乾淨啲

## 檔案結構

```
phonemouse/
  server.py          aiohttp app、WebSocket handler、token 驗證、工作列圖示邏輯
  winput.py          SendInput 包裝 (mouse_move, click, scroll, type_text, key_combo, media)
  traymenu.py        用 ctypes 直接寫嘅工作列圖示 (Shell_NotifyIcon),唔使 pystray/Pillow
  static/index.html  手機介面
  static/manifest.json + icon-*.png   加到主畫面用
  static/tray.ico    工作列圖示檔案
  config.json        port / token / 靈敏度等設定 (第一次執行自動產生)
  cert.pem / key.pem 自簽發 TLS 證書 (第一次執行自動產生,已加入 .gitignore)
  requirements.txt
  install.ps1        (方式 B) 建 venv、裝依賴、加防火牆規則
  start.bat          (方式 B) 雙擊啟動,顯示 QR code 後轉背景行
  build_exe.ps1      (方式 B) 用 PyInstaller 建構 dist\AirMouse.exe
  AirMouse.spec      PyInstaller 建構設定
  setup_autostart_exe.ps1  (方式 A) 幫 AirMouse.exe 設定開機自動以管理員身份啟動
```

## 疑難排解

- **手機開唔到網頁**:確認手機同電腦連緊同一個 Wi‑Fi,同埋防火牆規則
  有冇成功加入(可以喺「Windows Defender 防火牆」→「進階設定」入面搵
  `AirMouse` 條規則確認)。
- **連得到網頁但撳鍵/移動冇反應**:多數係 WebSocket token 驗證失敗,
  試下重新掃一次 QR code,或者清咗 Safari 嘅網站資料再開一次。
- **中文打唔到 / 打出嚟係亂碼**:呢個係用 `KEYEVENTF_UNICODE` 直接送字符,
  理論上任何應用程式(包括 Notepad、瀏覽器)都應該支援;如果個別遊戲或
  舊式程式唔支援 Unicode 輸入,可能要用返實體鍵盤。
- **升級之後主畫面圖示打唔開**:如果你係喺加咗 HTTPS 之前就已經「加到
  主畫面」,舊嘅圖示會指住已經失效嘅 `http://` 網址。刪除舊圖示,重新
  用 Safari 開新嘅 `https://` 網址(或者重新掃 QR code),再加一次落
  主畫面就得。
- **搵唔到工作列圖示**:Windows 對第一次出現嘅程式,通常會將個圖示收埋
  喺工作列右下角「顯示隱藏的圖示」(向上箭嘴 ^)入面,唔係直接常駐顯示。
  撳個箭嘴就搵到,想佢常駐顯示可以喺箭嘴嗰個選單度將 AirMouse 拖出嚟,
  或者去 Windows 設定 →「個人化」→「工作列」→「選擇要在工作列上顯示的
  圖示」度手動開返佢。

## 授權條款

[MIT](LICENSE)
