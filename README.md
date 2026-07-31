# 👹 天堂W BOSS 雙端雲端監控與即時時間軸系統 (Lineage W Boss Tracker)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.0%2B-green.svg)](https://pypi.org/project/PySide6/)
[![PWA](https://img.shields.io/badge/PWA-Supported-purple.svg)](https://developer.mozilla.org/en-US/docs/Web/PWA)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

本專案為一套專為《天堂W》血盟設計的 **AI 自動對話辨識 (OCR) + 雲端即時同步 BOSS 重生計時系統**。包含 **Windows 桌面端自動監控程式 (Python PySide6)** 與 **手機/電腦 Web PWA 行動端介面**。

---

## 🌟 核心特色與亮點

### 🖥️ 1. Windows 桌面監控端 (Python Desktop App)
- **多視窗自動偵測**：自動辨識並同時捕捉多個《天堂W》遊戲視窗。
- **純 Win32 CTypes 原生 GDI 擷圖**：後台視窗繪圖絕不卡頓，**連續運行 100+ 小時零 GDI Handle / 記憶體洩漏**。
- **PaddleOCR 高精準度辨識**：採用旗艦級中文 OCR 模型，結合黃色系統字色彩遮罩與二值化預處理，精準擷取頭目出現與擊敗訊息。
- **單行獨立抗性去重引擎**：訊息收回、刪除或修改時不影響去重機制，避免重複跳通知與訊息錯亂。
- **白名單保護與彈性同義字容錯**：
  - 含有 BOSS 名稱之訊息享有白名單免死金牌，**絕不受黑名單/萬用字元過濾條款誤殺**。
  - 支援 `擊`、`敗`、`死`、`消`、`倒`、`現`、`生`、`臨` 等自然語意同義字辨識。
- **非阻塞網路架構**：雲端 Ping 心跳與 OCR 主迴圈解耦，網路波動絕不卡死視窗擷圖。

### 📱 2. Web / PWA 行動端 (GitHub Pages Web App)
- **動態時間軸 (1小時 / 3小時 視角切換)**：
  - 提供 `⏱️ 1小時`（放大近距離）與 `⏱️ 3小時`（宏觀出王計畫）兩種視角切換。
  - **目前時間左側永遠維持 30 分鐘 (-30m)**，軸線頂部直接顯示 24H 絕對時鐘時間（如 `21:45` ➔ `目前 22:00` ➔ `22:15`）。
- **即時重生次序鏈 (Sequence Queue)**：照時間先後自動排序，顯示剩餘時間與各王怪預計點位。
- **獨立擊殺通報與自動歷史救援**：
  - 手機 PWA 點擊 `⚔️ 剛擊殺` 或 `🕒 指定時間` 可**直接獨立計算並同步至雲端**，即使電腦端離線也能流暢更新。
  - 帶有 **自動歷史通報救援引擎**，若資料庫時間意外清空，啟動時自動掃描歷程並還原倒數。
- **5 分鐘前雙重預警 (Sound + PWA Web Push)**：
  - 支援 Web Audio API 擬真晶片警報音效。
  - 完整支援 iOS 16.4+ Safari PWA 與 Android Chrome PWA 全螢幕原生推播。

---

## 🏗️ 系統架構圖 (Architecture)

```mermaid
flowchart TD
    subgraph Game ["🎮 遊戲視窗"]
        GW[天堂W 遊戲用戶端 (單/多開)]
    end

    subgraph Desktop ["🖥️ Windows 桌面端程式 (Python)"]
        GDI[Win32 CTypes GDI Capturer] -->|無損截圖| OCR[PaddleOCR 引擎 + 黃字濾鏡]
        OCR -->|提取對話| Dedup[單行獨立去重演算法]
        Dedup -->|頭目規則比對| BossTrack[BossTracker 狀態機]
        BossTrack -->|產生推播| WebPush[Web Push VAPID 發送器]
    end

    subgraph Cloud ["☁️ 雲端服務 (Firebase REST / Web Push)"]
        FB_DB[(Firebase Realtime Database)]
        VAPID[Web Push Service / FCM]
    end

    subgraph Mobile ["📱 行動端 / 網頁端 (GitHub Pages PWA)"]
        PWA[Web App / iOS Safari / Android Chrome]
        SW[ServiceWorker 背景推播]
    end

    GW -->|PrintWindow API| GDI
    BossTrack -->|REST PUT/PATCH| FB_DB
    WebPush -->|VAPID Push| VAPID
    VAPID -->|系統通知| SW
    SW -->|推播提醒| PWA
    PWA <-->|Realtime Socket / REST| FB_DB
    PWA -->|手動通報擊殺| FB_DB
```

---

## 🚀 快速開始 (Quick Start)

### 1. 桌面監控端環境準備 (Python Desktop)

#### 軟體需求
- Windows 10 / 11 64-bit
- Python 3.9+ (建議 3.10 或 3.11)

#### 安裝步驟
```bash
# 1. 複製專案
git clone https://github.com/alex43021/lineage-w-tracker.git
cd lineage-w-tracker

# 2. 建立並啟用 Python 虛擬環境 (選用但推薦)
python -m venv venv
venv\Scripts\activate

# 3. 安裝依賴套件
pip install -r requirements.txt

# 4. 啟動桌面端 GUI 程式
python main.py
```

---

### 2. 行動端 / 網頁端部署 (GitHub Pages PWA)

本專案 `web` 資料夾（或根目錄）可直接免費部署於 **GitHub Pages**：

1. 將本專案 Push 至您的 GitHub 儲存庫。
2. 進入 GitHub Repository 的 **Settings** ➔ **Pages**。
3. 在 **Branch** 選擇 `main`，資料夾選擇 `/root` 或 `/web` 並點擊 **Save**。
4. 部署完成後即可獲得 PWA 專屬網址（例如：`https://YOUR_USERNAME.github.io/lineage-w-tracker/`）。

#### 📱 加到手機桌面 (PWA 安裝)
- **iOS Safari**：點擊下方「分享」圖示 ➔ 選擇「加入主畫面」。
- **Android Chrome**：點擊右上角選單 ➔ 選擇「安裝應用程式」或「加到主畫面」。

---

## ⚙️ Firebase 資料庫配置指南 (Firebase Setup)

專案使用 **Firebase Realtime Database** 作為雲端同步中樞，設定完全免費：

1. 前往 [Firebase Console](https://console.firebase.google.com/) 並建立新專案。
2. 建立 **Realtime Database**，資料庫位置建議選擇 `asia-southeast1` (新加坡/亞洲)。
3. 在 **規則 (Rules)** 頁籤中，將規則修改為以下開放讀寫設定並點擊 **發布**：
   ```json
   {
     "rules": {
       ".read": true,
       ".write": true
     }
   }
   ```
4. 複製您的 Database URL（例如：`https://your-project-default-rtdb.asia-southeast1.firebasedatabase.app`）。
5. 於桌面端程式的 **⚙️ 系統設定** 中填入 URL 與血盟專屬通行碼 (Passcode) 即可！

---

## 📝 規則與過濾設定說明

### 👹 BOSS 規則設定
可在桌面端 GUI 靈活調整每隻 BOSS 的參數：
- **BOSS 名稱**：例如 `巴風特`。
- **出現關鍵字**：例如 `巴風特, 出現`。
- **擊敗關鍵字**：例如 `巴風特, 擊敗`。
- **計時 CD 時間 (分鐘)**：例如 `240` 分鐘（修改後自動重新計算當前下輪重生時間並同步雲端）。

### 🚫 排除訊息 (黑名單萬用字元)
在桌面端可設定過濾雜訊，支援 `*` 與 `?` 萬用字元，例如：
- `*獲得*`
- `*卡片*`
- `*已登入*`
- `*派遣*`

> 💡 **保護機制**：凡是包含 BOSS 名稱的對話，系統會自動享有白名單保護，**永遠不會被黑名單過濾掉**。

---

## 🛠️ 常見問題與疑難排解 (FAQ)

#### Q1: 為什麼手機上點擊通報擊殺後，重生時間還是舊的？
- 請確認您的手機已經連線至相同的 Firebase URL 與血盟通行碼。
- 專案已支援**網頁端獨立 CD 重算**，若先前桌面端有更改過 CD（如 480m 降為 240m），請在手機上重新整理網頁，系統會自動載入最新 CD 規則。

#### Q2: 桌面端長時間運行會不會卡頓或記憶體暴增？
- 不會！本專案採用**純 CTypes 原生 Win32 GDI HDC/HBITMAP 手動管理**與 `QTextCursor` 滾動控制，控制代碼恆定維持在 ~30 個，並有自動 OS Working Set 記憶體修剪機制。

#### Q3: 桌面端抓不到遊戲視窗怎麼辦？
- 請確保《天堂W》遊戲視窗**未處於最小化狀態**（支援背景遮擋或置於其他視窗下方）。
- 若遊戲以系統管理員權限執行，請同樣以 **系統管理員身份執行 `python main.py`**。

---

## 📄 授權條款 (License)

本專案採用 [MIT License](LICENSE) 開源授權，歡迎自由修改與衍生擴充。
