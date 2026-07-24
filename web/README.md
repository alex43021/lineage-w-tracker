# 天堂W BOSS 雲端動態時間軸網頁端 (GitHub Pages 部署指南)

本網頁端可獨立部署於 **GitHub Pages**、Netlify、Vercel 或任何靜態網頁伺服器，支援 **PWA 手機桌面快捷安裝**、**動態 3.5 小時時間軸**、**5 分鐘前推播與音效預警**。

---

## 🚀 快速部署至 GitHub Pages

### 方式一：將本專案的 `web` 資料夾設為 GitHub Pages 根目錄

1. 登入 GitHub 並建立一個新的公開或私有儲存庫（Repository），例如 `lineage-w-tracker`。
2. 將本專案的所有檔案（或將 `web` 資料夾內的檔案）Push 到該儲存庫的 `main` 或 `gh-pages` 分支：
   ```bash
   git init
   git add .
   git commit -m "Deploy Lineage W Tracker Web App"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/lineage-w-tracker.git
   git push -u origin main
   ```
3. 在 GitHub 儲存庫頁面點擊 **Settings** ➔ **Pages**。
4. 在 **Source** 選擇 `Deploy from a branch`：
   - 分支選擇 `main`
   - 資料夾選擇 `/web` (若您是把整包推上去) 或 `/root` (若直接將 web 內容放到根目錄)。
5. 點擊 **Save**。等待 1-2 分鐘後，即可獲得您的專屬網址（例如 `https://YOUR_USERNAME.github.io/lineage-w-tracker/`）！

---

## ✨ 核心功能特色

1. **動態時間軸 (Dynamic Timeline)**：
   - 跨度呈現 **前 30 分鐘 (-30m)** 至 **後 3 小時 (+3h)**。
   - 紅色發光「現在」時間線每秒動態推進。
   - 自動將全數 BOSS 重生時間標記在時間軸軸線上（5分鐘內發光警示、30分鐘內亮綠標記）。

2. **5 分鐘前雙重預警 (Sound + PWA / Web Push)**：
   - 當任何 BOSS 距離重生剩餘 5 分鐘時，自動觸發高低音雙聲道音效 alert（Web Audio API 擬真晶片音效）。
   - 自動觸發原生系統推播提醒（支援 Windows 桌面推播與 iOS/Android 手機 PWA 推播）。

3. **PWA 手機全螢幕 App 支援**：
   - 在 iOS Safari 點擊「分享 ➔ 加入主畫面」或在 Android Chrome 點擊「安裝應用程式」。
   - 可像原生 App 一樣以全螢幕開啟並接收即時推播。

4. **成員手動擊殺/死亡通報**：
   - 任何血盟成員皆可透過手機點擊任意 BOSS 卡片上的 `⚔️ 手動通報`。
   - 通報會即時同步至 Firebase，電腦端 Windows 主程式與所有成員手機畫面會立即更新倒數時間！
