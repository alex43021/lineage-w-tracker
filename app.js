// Global State Variables
let db = null;
let firebaseApp = null;
let currentPasscode = "123456789";
let currentDbUrl = "https://wchat-6ea90-default-rtdb.asia-southeast1.firebasedatabase.app/";
let bossStates = {};
let bossRules = [];
let localTimers = {};
let notifiedSpawns = new Set(); // Prevent duplicate 5-minute notifications for the same spawn
let notifyEnabled = true;
let currentBossFilter = "all";
let selectedBossForReport = null;
let deferredPrompt = null;

// Intercept browser PWA install prompt
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
});

// Register PWA Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('service-worker.js')
      .then(reg => console.log('PWA Service Worker registered:', reg.scope))
      .catch(err => console.error('Service Worker registration failed:', err));
  });
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  setupUIEventListeners();
  updateTimelineScale();
  
  // Start 1-second interval timer for live countdowns & timeline indicator
  setInterval(tickRealtimeLoop, 1000);
  
  loadConfigAndConnect();
});

// Load configuration & connect to Firebase
async function loadConfigAndConnect() {
  try {
    const response = await fetch('data/firebase_config.json');
    if (response.ok) {
      const config = await response.json();
      currentDbUrl = (config.databaseURL || currentDbUrl).replace(/\/$/, "");
      currentPasscode = config.passcode || currentPasscode;
    }
  } catch (e) {
    console.log("data/firebase_config.json not found, using defaults or localStorage.");
  }

  // Check localStorage overrides
  const savedUrl = localStorage.getItem('lw_db_url');
  const savedCode = localStorage.getItem('lw_passcode');
  if (savedUrl) currentDbUrl = savedUrl.replace(/\/$/, "");
  if (savedCode) currentPasscode = savedCode;

  initFirebase(currentDbUrl, currentPasscode);
}

// Direct REST API Fallback Fetch for Instant Rendering
async function fetchDirectRestData(url, passcode) {
  try {
    const cleanUrl = url.replace(/\/$/, "");
    const restUrl = `${cleanUrl}/lineage_w_tracker/${passcode}/boss_states.json`;
    const res = await fetch(restUrl);
    if (res.ok) {
      const data = await res.json();
      if (data && typeof data === 'object') {
        bossStates = data;
        updateConnectionStatus('online');
        renderBossGrid();
        updateTimeline();
        renderSequenceQueue();
      }
    }
  } catch (e) {
    console.log("REST fallback fetch failed:", e);
  }
}

// Initialize Firebase Realtime Database
function initFirebase(url, passcode) {
  currentDbUrl = url.replace(/\/$/, "");
  currentPasscode = passcode || "123456789";

  updateConnectionStatus('connecting');

  // 1. Direct REST fetch for immediate 200ms rendering
  fetchDirectRestData(currentDbUrl, currentPasscode);

  if (db) {
    try {
      db.ref(`lineage_w_tracker/${currentPasscode}/boss_states`).off();
      db.ref(`lineage_w_tracker/${currentPasscode}/boss_rules`).off();
    } catch(e){}
  }

  try {
    if (firebaseApp) {
      try { firebaseApp.delete(); } catch(e){}
    }

    firebaseApp = firebase.initializeApp({ databaseURL: currentDbUrl }, "LW-Tracker-" + Date.now());
    db = firebaseApp.database();

    // 2. Start realtime sync listeners immediately
    startSyncListeners();

    // 3. Monitor socket connection status
    db.ref('.info/connected').on('value', (snap) => {
      if (snap.val() === true) {
        updateConnectionStatus('online');
        localStorage.setItem('lw_db_url', currentDbUrl);
        localStorage.setItem('lw_passcode', currentPasscode);
      }
    });
  } catch (e) {
    console.error("Firebase init failed:", e);
  }
}

// Start realtime sync listeners for boss_states
function startSyncListeners() {
  if (!db) return;

  // 1. Sync BOSS States
  db.ref(`lineage_w_tracker/${currentPasscode}/boss_states`).on('value', (snapshot) => {
    const data = snapshot.val();
    if (data && typeof data === 'object') {
      bossStates = data;
      updateConnectionStatus('online');
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();
    }
  });

  // 2. Sync BOSS Rules
  db.ref(`lineage_w_tracker/${currentPasscode}/boss_rules`).on('value', (snapshot) => {
    const data = snapshot.val();
    if (Array.isArray(data)) {
      bossRules = data;
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();
    }
  });
}

// Connection Status Indicator
function updateConnectionStatus(status) {
  const statusEl = document.getElementById('connectionStatus');
  if (!statusEl) return;
  const textEl = statusEl.querySelector('.status-text');

  statusEl.className = 'status-badge';
  if (status === 'online') {
    statusEl.classList.add('status-online');
    if (textEl) textEl.textContent = '雲端連線中';
  } else if (status === 'connecting') {
    statusEl.classList.add('status-offline');
    if (textEl) textEl.textContent = '連線中...';
  } else {
    statusEl.classList.add('status-offline');
    if (textEl) textEl.textContent = '未連線';
  }
}

/* ==========================================================================
   CROSS-BROWSER GUARANTEED LOCAL TIME PARSER & COOLDOWN LOOKUP
   ========================================================================== */

function parseIsoToEpochMs(dateStr) {
  if (!dateStr) return null;
  if (typeof dateStr === 'number') return dateStr;

  const str = String(dateStr).trim();
  
  if (str.includes('Z') || /[+-]\d{2}:\d{2}$/.test(str)) {
    const ms = Date.parse(str);
    return isNaN(ms) ? null : ms;
  }

  const match = str.match(/^(\d{4})[-/](\d{1,2})[-/](\d{1,2})[T\s](\d{1,2}):(\d{2})(?::(\d{2}))?/);
  if (match) {
    const year = parseInt(match[1], 10);
    const month = parseInt(match[2], 10) - 1;
    const day = parseInt(match[3], 10);
    const hour = parseInt(match[4], 10);
    const min = parseInt(match[5], 10);
    const sec = parseInt(match[6] || '0', 10);
    return new Date(year, month, day, hour, min, sec).getTime();
  }

  const fallbackMs = Date.parse(str);
  return isNaN(fallbackMs) ? null : fallbackMs;
}

function formatLocalTime24(dateObjOrIsoStr) {
  if (!dateObjOrIsoStr) return '--:--';
  const ms = parseIsoToEpochMs(dateObjOrIsoStr);
  if (!ms) return '--:--';
  const d = new Date(ms);
  const hh = String(d.getHours()).padStart(2, '0');
  const mm = String(d.getMinutes()).padStart(2, '0');
  return `${hh}:${mm}`;
}

function getBossCooldownMins(bossName) {
  if (Array.isArray(bossRules) && bossRules.length > 0) {
    const rule = bossRules.find(r => r.name === bossName);
    if (rule && rule.cooldown_mins) {
      return rule.cooldown_mins;
    }
  }
  if (bossStates[bossName] && bossStates[bossName].cooldown_mins) {
    return bossStates[bossName].cooldown_mins;
  }
  return 60;
}

function getEffectiveBossState(boss, nowMs = Date.now()) {
  let isOverdue = boss.is_overdue || false;
  let displayName = boss.name;

  let spawnMs = parseIsoToEpochMs(boss.next_spawn_time);
  const cooldownMins = getBossCooldownMins(boss.name);
  const cooldownMs = cooldownMins * 60 * 1000;

  if (spawnMs && !isNaN(spawnMs)) {
    if (spawnMs <= nowMs && boss.status !== 'alive') {
      isOverdue = true;
      // Auto roll forward to the next cycle using exact boss cooldown
      while (spawnMs <= nowMs) {
        spawnMs += cooldownMs;
      }
    }
  }

  if (isOverdue) {
    displayName = `${boss.name}(過)`;
  }

  return {
    displayName,
    spawnMs,
    cooldownMins,
    cooldownMs,
    isOverdue
  };
}

/* ==========================================================================
   DYNAMIC INTERACTIVE TIMELINE SYSTEM (-30m ~ NOW ~ +3h)
   Completing ALL boss events in the 3.5-hour range (-30m ~ +3h) with 3-tier staggering!
   ========================================================================== */

function updateTimelineScale(nowMs = Date.now()) {
  const scaleEl = document.getElementById('timelineScale');
  if (!scaleEl) return;

  // Scale ticks displaying absolute 24-Hour clock times: -30m, -15m, NOW, +15m, +30m, +1h, +1.5h, +2h, +2.5h, +3h
  const ticks = [
    { offsetMins: -30, pct: 0 },
    { offsetMins: -15, pct: 7.14 },
    { offsetMins: 0, pct: 14.28, isNow: true },
    { offsetMins: 15, pct: 21.42 },
    { offsetMins: 30, pct: 28.57 },
    { offsetMins: 60, pct: 42.85 },
    { offsetMins: 90, pct: 57.14 },
    { offsetMins: 120, pct: 71.42 },
    { offsetMins: 150, pct: 85.71 },
    { offsetMins: 180, pct: 100 }
  ];

  scaleEl.innerHTML = '';
  ticks.forEach(t => {
    const tickMs = nowMs + (t.offsetMins * 60 * 1000);
    const timeStr = formatLocalTime24(tickMs);
    const div = document.createElement('div');
    div.className = 'scale-tick' + (t.isNow ? ' now-tick' : '');
    div.style.left = `${t.pct}%`;
    div.textContent = t.isNow ? `目前 ${timeStr}` : timeStr;
    scaleEl.appendChild(div);
  });
}

function updateTimeline() {
  const layer = document.getElementById('timelineMarkersLayer');
  const nowInd = document.getElementById('nowIndicator');
  const nowText = document.getElementById('nowTimeText');

  if (!layer) return;

  const now = new Date();
  const nowMs = now.getTime();

  // Update 24H scale header labels
  updateTimelineScale(nowMs);

  if (nowText) {
    nowText.textContent = now.toTimeString().split(' ')[0];
  }

  // Fixed NOW position at 14.28% (30 mins into 210 min scale)
  const nowPct = 14.28;
  if (nowInd) {
    nowInd.style.left = `${nowPct}%`;
  }

  const windowStartMs = nowMs - (30 * 60 * 1000); // -30m
  const windowEndMs = nowMs + (180 * 60 * 1000);  // +180m (3h)
  const totalWindowMs = 210 * 60 * 1000;

  layer.innerHTML = '';

  const markerItems = [];

  // Evaluate EVERY boss for past death events AND future spawn cycles in the 3.5h window!
  Object.values(bossStates).forEach(boss => {
    const cooldownMins = getBossCooldownMins(boss.name);
    const cooldownMs = cooldownMins * 60 * 1000;

    // 1. Check last_death_time (Past death event in -30m ~ +3h)
    if (boss.last_death_time) {
      const deathMs = parseIsoToEpochMs(boss.last_death_time);
      if (deathMs && deathMs >= windowStartMs && deathMs <= windowEndMs) {
        const pct = ((deathMs - windowStartMs) / totalWindowMs) * 100;
        const diffSec = Math.floor((deathMs - nowMs) / 1000);
        markerItems.push({
          boss,
          targetTimeMs: deathMs,
          pct,
          diffSec,
          eventType: 'death',
          displayText: boss.name
        });
      }
    }

    // 2. Check effective next_spawn_time AND future recurring spawn cycles (with overdue auto-roll)
    const eff = getEffectiveBossState(boss, nowMs);
    if (eff.spawnMs) {
      let spawnMs = eff.spawnMs;
      while (spawnMs <= windowEndMs) {
        if (spawnMs >= windowStartMs) {
          const pct = ((spawnMs - windowStartMs) / totalWindowMs) * 100;
          const diffSec = Math.floor((spawnMs - nowMs) / 1000);
          markerItems.push({
            boss,
            targetTimeMs: spawnMs,
            pct,
            diffSec,
            eventType: 'spawn',
            displayText: `${eff.displayName} ${formatLocalTime24(spawnMs)}`
          });
        }
        if (cooldownMs <= 0) break;
        spawnMs += cooldownMs;
      }
    }
  });

  // Deduplicate marker items with same boss and exact same target time
  const uniqueMarkers = [];
  const seenKeys = new Set();
  markerItems.forEach(item => {
    const key = `${item.boss.name}_${item.eventType}_${item.targetTimeMs}`;
    if (!seenKeys.has(key)) {
      seenKeys.add(key);
      uniqueMarkers.push(item);
    }
  });

  // Sort by position percentage ascending
  uniqueMarkers.sort((a, b) => a.pct - b.pct);

  // Assign 3-tier vertical staggering (0, 1, 2) to adjacent pins to prevent horizontal overlap
  let currentTier = 0;
  let prevPct = -999;
  uniqueMarkers.forEach(item => {
    if (item.pct - prevPct < 7) {
      currentTier = (currentTier + 1) % 3;
    } else {
      currentTier = 0;
    }
    prevPct = item.pct;
    item.tier = currentTier;
  });

  // Render all unique markers
  uniqueMarkers.forEach(item => {
    const marker = document.createElement('div');
    marker.className = `timeline-marker tier-${item.tier}`;
    marker.style.left = `${item.pct}%`;

    let statusClass = 'marker-future';
    if (item.diffSec < 0) {
      statusClass = 'marker-past';
    } else if (item.diffSec <= 300) { // < 5 mins
      statusClass = 'marker-warning';
    } else if (item.diffSec <= 1800) { // < 30 mins
      statusClass = 'marker-soon';
    }

    marker.classList.add(statusClass);

    marker.innerHTML = `
      <div class="marker-content">
        <div class="marker-dot"></div>
        <div class="marker-label">${item.displayText}</div>
      </div>
    `;

    marker.addEventListener('click', () => {
      highlightBossCard(item.boss.name);
    });

    layer.appendChild(marker);
  });
}

/* ==========================================================================
   CHRONOLOGICAL SEQUENCE QUEUE (密集 BOSS 順序鏈)
   ========================================================================== */

function renderSequenceQueue() {
  const container = document.getElementById('sequenceQueueList');
  if (!container) return;

  const nowMs = Date.now();
  const upcomingBosses = [];

  Object.values(bossStates).forEach(boss => {
    const eff = getEffectiveBossState(boss, nowMs);
    if (!eff.spawnMs) return;

    const diffSec = Math.floor((eff.spawnMs - nowMs) / 1000);
    // Include upcoming bosses in next 3 hours
    if (diffSec >= -300 && diffSec <= 3 * 3600) {
      upcomingBosses.push({ boss, displayName: eff.displayName, spawnMs: eff.spawnMs, diffSec });
    }
  });

  if (upcomingBosses.length === 0) {
    container.innerHTML = '<div class="loading-state">目前無即將重生的 BOSS</div>';
    return;
  }

  // Sort by spawn time ascending
  upcomingBosses.sort((a, b) => a.spawnMs - b.spawnMs);

  container.innerHTML = '';
  upcomingBosses.forEach((item, index) => {
    const card = document.createElement('div');
    let itemClass = 'seq-item';
    if (item.diffSec > 0 && item.diffSec <= 300) {
      itemClass += ' seq-item-warning';
    } else if (item.diffSec > 300 && item.diffSec <= 1800) {
      itemClass += ' seq-item-soon';
    }
    card.className = itemClass;

    const timeStr = formatLocalTime24(item.spawnMs);
    let diffStr = '已重生';
    if (item.diffSec > 0) {
      const m = Math.floor(item.diffSec / 60);
      diffStr = `剩 ${m} 分`;
    }

    card.innerHTML = `
      <span class="seq-idx">#${index + 1}</span>
      <span class="seq-name">👹 ${item.displayName}</span>
      <span class="seq-time">${timeStr}</span>
      <span class="seq-diff">(${diffStr})</span>
      ${index < upcomingBosses.length - 1 ? '<span class="seq-arrow">➔</span>' : ''}
    `;

    card.addEventListener('click', () => {
      highlightBossCard(item.boss.name);
    });

    container.appendChild(card);
  });
}

function highlightBossCard(bossName) {
  const cards = document.querySelectorAll('.boss-card');
  cards.forEach(card => {
    if (card.dataset.bossName === bossName) {
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      card.classList.add('warning-card');
      setTimeout(() => card.classList.remove('warning-card'), 2500);
    }
  });
}

/* ==========================================================================
   5-MINUTE ADVANCE WARNING SYSTEM & BULLETPROOF WINDOWS TOAST NOTIFICATIONS
   ========================================================================== */

function checkAdvanceWarnings(nowMs) {
  Object.values(bossStates).forEach(boss => {
    const eff = getEffectiveBossState(boss, nowMs);
    if (!eff.spawnMs) return;

    const diffSec = Math.floor((eff.spawnMs - nowMs) / 1000);

    // Trigger warning when BOSS is between 1s and 300s (5 minutes) away
    if (diffSec > 0 && diffSec <= 300) {
      const spawnKey = `${boss.name}_${eff.spawnMs}`;
      if (!notifiedSpawns.has(spawnKey)) {
        notifiedSpawns.add(spawnKey);
        triggerBoss5MinWarning(boss, diffSec, eff.spawnMs, eff.displayName);
      }
    }
  });
}

function sendNativeNotification(title, body, tag = null) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;

  const iconUrl = new URL('icons/icon-192.png', window.location.href).href;
  const options = {
    body: body,
    icon: iconUrl,
    badge: iconUrl,
    tag: tag || ('boss_notify_' + Date.now()),
    requireInteraction: true,
    silent: false
  };

  // Use ServiceWorker showNotification ONLY if SW controller is active, else fallback to direct Notification API
  if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification(title, options).catch(err => {
        console.log("SW showNotification error, falling back:", err);
        new Notification(title, options);
      });
    });
  } else {
    try {
      const n = new Notification(title, options);
      n.onclick = () => { window.focus(); };
    } catch (e) {
      console.log("Direct Notification API error:", e);
    }
  }
}

function requestAndTestNotification() {
  if (!('Notification' in window)) {
    alert("您的瀏覽器不支援 Notification 系統推播功能。");
    return;
  }

  if (Notification.permission === 'granted') {
    triggerTestNotification();
  } else if (Notification.permission === 'denied') {
    alert("【Chrome 通知目前被封鎖】\n\n請在 Chrome 網址列左側點擊 🔒 鎖頭圖示 ➔ 找到【通知 (Notifications)】➔ 選擇【允許 (Allow)】後重新整理頁面！");
  } else {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        triggerTestNotification();
      } else {
        alert("已拒絕通知權限。若想開啟，請點擊 Chrome 網址列左側 🔒 鎖頭圖示允許通知。");
      }
    });
  }
}

function triggerTestNotification() {
  const title = "🔔 [BOSS 預警] 通知功能測試成功！";
  const body = "當 BOSS 重生倒數剩餘 5 分鐘時，將會自動發送 Windows 右下角通知提醒。";
  
  sendNativeNotification(title, body, "test_notification");

  alert("🎉 已觸發測試推播！\n\n若 Windows 右下角仍未出現浮動橫幅，請確認：\n1. Windows 右下角【專注輔助 / 請勿打擾】是否已關閉。\n2. Windows 設定 ➔【系統】➔【通知與動作】中，【Google Chrome】是否有開啟！");
}

function triggerBoss5MinWarning(boss, secondsLeft, spawnMs, displayName) {
  const minsLeft = Math.ceil(secondsLeft / 60);
  const spawnTimeStr = formatLocalTime24(spawnMs);
  const nameToUse = displayName || boss.name;
  const title = `🔔 [BOSS 預警] ${nameToUse}`;
  const body = `即將在 ${minsLeft} 分鐘後 (${spawnTimeStr}) 出現！請血盟成員準備！`;

  if (notifyEnabled) {
    sendNativeNotification(title, body, boss.name);
  }
}

/* ==========================================================================
   REALTIME LOOP (Runs every second)
   ========================================================================== */

function tickRealtimeLoop() {
  const nowMs = Date.now();

  checkAdvanceWarnings(nowMs);
  updateTimeline();
  renderSequenceQueue();
  updateCardCountdowns(nowMs);
}

function updateCardCountdowns(nowMs) {
  const cards = document.querySelectorAll('.boss-card');
  cards.forEach(card => {
    const bossName = card.dataset.bossName;
    const boss = bossStates[bossName];
    if (!boss) return;

    const timerEl = card.querySelector('.countdown-text');
    const nameEl = card.querySelector('.boss-name');
    if (!timerEl) return;

    const eff = getEffectiveBossState(boss, nowMs);
    if (nameEl) nameEl.textContent = `👹 ${eff.displayName}`;

    if (eff.spawnMs) {
      const diffSec = Math.floor((eff.spawnMs - nowMs) / 1000);

      if (diffSec > 0) {
        const m = Math.floor(diffSec / 60);
        const s = diffSec % 60;
        timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

        if (diffSec <= 300) {
          card.classList.add('warning-card');
        } else {
          card.classList.remove('warning-card');
        }
      } else {
        timerEl.textContent = '已重生';
        card.classList.remove('warning-card');
      }
    }
  });
}

/* ==========================================================================
   BOSS GRID & CARDS RENDERING
   ========================================================================== */

function renderBossGrid() {
  const grid = document.getElementById('bossGrid');
  const countBadge = document.getElementById('bossCountBadge');
  if (!grid) return;

  const bosses = Object.values(bossStates);
  if (countBadge) countBadge.textContent = `${bosses.length} 個`;

  if (bosses.length === 0) {
    grid.innerHTML = '<div class="loading-state">尚無 BOSS 時間狀態資料</div>';
    return;
  }

  // Filter bosses based on current selection
  let filtered = bosses;
  const nowMs = Date.now();

  if (currentBossFilter === 'soon') {
    filtered = bosses.filter(b => {
      const eff = getEffectiveBossState(b, nowMs);
      if (!eff.spawnMs) return false;
      const diffMs = eff.spawnMs - nowMs;
      return diffMs > 0 && diffMs <= 30 * 60 * 1000;
    });
  } else if (currentBossFilter === 'alive') {
    filtered = bosses.filter(b => b.status === 'alive');
  }

  // Sort by next_spawn_time ascending
  filtered.sort((a, b) => {
    const tA = getEffectiveBossState(a, nowMs).spawnMs || Infinity;
    const tB = getEffectiveBossState(b, nowMs).spawnMs || Infinity;
    return tA - tB;
  });

  grid.innerHTML = '';
  filtered.forEach(boss => {
    const eff = getEffectiveBossState(boss, nowMs);
    const card = document.createElement('div');
    const stateClass = `state-${boss.status || 'unknown'}`;
    card.className = `boss-card ${stateClass}`;
    card.dataset.bossName = boss.name;

    const lastDeathStr = boss.last_death_time ? formatLocalTime24(boss.last_death_time) : (eff.isOverdue && eff.spawnMs ? `${formatLocalTime24(eff.spawnMs - eff.cooldownMs)} (推算)` : '--:--');
    const nextSpawnStr = eff.spawnMs ? formatLocalTime24(eff.spawnMs) : '--:--';
    const statusText = boss.status === 'alive' ? '已出現' : (boss.status === 'dead' ? '倒數中' : (eff.isOverdue ? '倒數中(過)' : '未知'));

    card.innerHTML = `
      <div class="boss-info">
        <span class="boss-name">👹 ${eff.displayName}</span>
        <span class="boss-status-label">${statusText}</span>
      </div>
      <div class="boss-timer-container">
        <div class="countdown-text">--:--</div>
      </div>
      <div class="boss-time-details">
        <div class="time-row"><span>預計重生：</span><strong>${nextSpawnStr}</strong></div>
        <div class="time-row"><span>上次死亡：</span><span>${lastDeathStr} (${boss.reported_by || '系統'})</span></div>
      </div>
      <div class="boss-card-actions">
        <button class="btn btn-quick-kill" onclick="quickReportKillNow('${boss.name}')" title="一鍵通報剛剛擊殺 (現在時間)">
          ⚔️ 剛擊殺
        </button>
        <button class="btn btn-custom-time" onclick="openReportModal('${boss.name}')" title="指定歷史擊殺時間">
          🕒 指定時間
        </button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function quickReportKillNow(bossName) {
  if (!bossName) return;

  const reporterName = '成員';
  const now = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  const localIso = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;

  const reportId = 'rep_' + Date.now();
  const reportData = {
    boss_name: bossName,
    reported_by: reporterName,
    time_type: 'now',
    custom_time: `${pad(now.getHours())}:${pad(now.getMinutes())}`,
    passcode: currentPasscode,
    timestamp: localIso,
    status: 'dead'
  };

  const cleanUrl = currentDbUrl.replace(/\/$/, "");
  const reportUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/reports/${reportId}.json`;
  
  fetch(reportUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reportData)
  })
  .then(res => {
    if (res.ok) {
      alert(`🎉 已通報 ${bossName} 剛剛擊殺！系統已廣播時間給所有成員。`);
      fetchDirectRestData(currentDbUrl, currentPasscode);
    } else {
      alert('通報失敗，請確認網路連線。');
    }
  })
  .catch(err => {
    alert('通報發生錯誤：' + err.message);
  });
}

/* ==========================================================================
   MANUAL REPORT MODAL & EVENT LISTENERS
   ========================================================================== */

function populate24hTimeSelectors() {
  const hourSelect = document.getElementById('customHour');
  const minuteSelect = document.getElementById('customMinute');
  if (!hourSelect || !minuteSelect) return;

  if (hourSelect.children.length === 0) {
    hourSelect.innerHTML = '';
    for (let i = 0; i < 24; i++) {
      const opt = document.createElement('option');
      const hh = String(i).padStart(2, '0');
      opt.value = hh;
      opt.textContent = `${hh} 時`;
      hourSelect.appendChild(opt);
    }
  }

  if (minuteSelect.children.length === 0) {
    minuteSelect.innerHTML = '';
    for (let i = 0; i < 60; i++) {
      const opt = document.createElement('option');
      const mm = String(i).padStart(2, '0');
      opt.value = mm;
      opt.textContent = `${mm} 分`;
      minuteSelect.appendChild(opt);
    }
  }
}

function openReportModal(bossName) {
  selectedBossForReport = bossName;
  document.getElementById('reportBossName').textContent = `指定擊殺時間：${bossName}`;

  // Default to "custom" radio option when opening custom time modal
  const customRadio = document.querySelector('input[name="timeType"][value="custom"]');
  if (customRadio) customRadio.checked = true;
  
  const customGroup = document.getElementById('customTimeGroup');
  if (customGroup) customGroup.style.display = 'flex';

  // Populate & Pre-fill 24h hour and minute dropdowns
  populate24hTimeSelectors();
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const hourSelect = document.getElementById('customHour');
  const minuteSelect = document.getElementById('customMinute');
  if (hourSelect) hourSelect.value = hh;
  if (minuteSelect) minuteSelect.value = mm;

  showModal('reportModal');
}

function centerTimelineNow() {
  const wrapper = document.getElementById('timelineWrapper');
  const track = document.getElementById('timelineTrackContainer');
  if (!wrapper || !track) return;

  const trackWidth = track.offsetWidth;
  const wrapperWidth = wrapper.offsetWidth;
  const nowPx = trackWidth * 0.1428;
  const scrollPos = nowPx - (wrapperWidth / 2);

  wrapper.scrollTo({
    left: Math.max(0, scrollPos),
    behavior: 'smooth'
  });
}

function setupUIEventListeners() {
  // Mobile Tab Switcher
  document.querySelectorAll('.mobile-tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.mobile-tab-btn').forEach(b => b.classList.remove('active'));
      e.currentTarget.classList.add('active');

      const tab = e.currentTarget.dataset.tab;
      const timelineSec = document.getElementById('tabContentTimeline');
      const bossSec = document.getElementById('tabContentBosses');

      if (tab === 'timeline') {
        if (timelineSec) timelineSec.classList.add('active');
        if (bossSec) bossSec.classList.remove('active');
        setTimeout(centerTimelineNow, 100);
      } else if (tab === 'bosses') {
        if (bossSec) bossSec.classList.add('active');
        if (timelineSec) timelineSec.classList.remove('active');
      }
    });
  });

  // Center NOW Button
  document.getElementById('centerNowBtn')?.addEventListener('click', centerTimelineNow);

  // PWA Mobile Install Button
  document.getElementById('pwaInstallBtn')?.addEventListener('click', async () => {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      console.log(`User choice on PWA install: ${outcome}`);
      deferredPrompt = null;
    } else {
      showModal('pwaModal');
    }
  });

  document.getElementById('closePwaBtn')?.addEventListener('click', () => hideModal('pwaModal'));
  document.getElementById('confirmPwaBtn')?.addEventListener('click', () => hideModal('pwaModal'));

  // Radio button toggle for time type in manual report modal
  document.querySelectorAll('input[name="timeType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const customGroup = document.getElementById('customTimeGroup');
      if (customGroup) {
        if (e.target.value === 'custom') {
          customGroup.style.display = 'flex';
          populate24hTimeSelectors();
          const now = new Date();
          const hh = String(now.getHours()).padStart(2, '0');
          const mm = String(now.getMinutes()).padStart(2, '0');
          const hourSelect = document.getElementById('customHour');
          const minuteSelect = document.getElementById('customMinute');
          if (hourSelect && !hourSelect.value) hourSelect.value = hh;
          if (minuteSelect && !minuteSelect.value) minuteSelect.value = mm;
        } else {
          customGroup.style.display = 'none';
        }
      }
    });
  });

  // Notification Toggle Button in Header
  document.getElementById('notifyToggleBtn')?.addEventListener('click', (e) => {
    notifyEnabled = !notifyEnabled;
    const btn = e.currentTarget;
    btn.classList.toggle('active', notifyEnabled);
    btn.querySelector('.pill-text').textContent = notifyEnabled ? '5分鐘預警: 開啟' : '5分鐘預警: 關閉';

    if (notifyEnabled) {
      requestAndTestNotification();
    }
  });

  // Direct Test Notification Button in Header
  document.getElementById('testPushBtn')?.addEventListener('click', () => {
    requestAndTestNotification();
  });

  // Boss Filter Buttons
  document.querySelectorAll('[data-boss-filter]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('[data-boss-filter]').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentBossFilter = e.target.dataset.bossFilter;
      renderBossGrid();
    });
  });

  // Manual Report Form Submission
  document.getElementById('closeReportBtn')?.addEventListener('click', () => hideModal('reportModal'));
  document.getElementById('cancelReportBtn')?.addEventListener('click', () => hideModal('reportModal'));
  document.getElementById('submitReportBtn')?.addEventListener('click', submitManualReport);
}

function submitManualReport() {
  if (!selectedBossForReport) return;

  const reporterName = document.getElementById('reporterName')?.value?.trim() || '成員';
  const timeType = document.querySelector('input[name="timeType"]:checked')?.value || 'now';

  const d = new Date();
  let customVal = '';

  if (timeType === 'custom') {
    const hh = document.getElementById('customHour')?.value || '00';
    const mm = document.getElementById('customMinute')?.value || '00';
    customVal = `${hh}:${mm}`;
    d.setHours(parseInt(hh, 10), parseInt(mm, 10), 0, 0);
  }

  const pad = (n) => String(n).padStart(2, '0');
  const localIso = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

  const reportId = 'rep_' + Date.now();
  const reportData = {
    boss_name: selectedBossForReport,
    reported_by: reporterName,
    time_type: timeType,
    custom_time: customVal,
    passcode: currentPasscode,
    timestamp: localIso,
    status: 'dead'
  };

  // REST PUT for guaranteed submission
  const cleanUrl = currentDbUrl.replace(/\/$/, "");
  const reportUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/reports/${reportId}.json`;
  
  fetch(reportUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reportData)
  })
  .then(res => {
    if (res.ok) {
      alert(`🎉 成功通報 ${selectedBossForReport} 已擊殺！系統將自動廣播給所有用戶。`);
      hideModal('reportModal');
      fetchDirectRestData(currentDbUrl, currentPasscode);
    } else {
      alert('通報失敗，請確認網路連線。');
    }
  })
  .catch(err => {
    alert('通報發生錯誤：' + err.message);
  });
}

function showModal(id) {
  document.getElementById(id)?.classList.add('show');
}
function hideModal(id) {
  document.getElementById(id)?.classList.remove('show');
}
