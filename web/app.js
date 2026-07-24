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
  initTimelineScale();
  
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
   DYNAMIC INTERACTIVE TIMELINE SYSTEM (-30m ~ NOW ~ +3h)
   Includes 3-Tier Vertical Marker Staggering to prevent text overlap!
   ========================================================================== */

function initTimelineScale() {
  const scaleEl = document.getElementById('timelineScale');
  if (!scaleEl) return;

  // Scale labels: -30m, -15m, NOW, +15m, +30m, +1h, +1.5h, +2h, +2.5h, +3h
  const ticks = [
    { text: '-30m', pct: 0 },
    { text: '-15m', pct: 7.14 },
    { text: '目前 (NOW)', pct: 14.28, isNow: true },
    { text: '+15m', pct: 21.42 },
    { text: '+30m', pct: 28.57 },
    { text: '+1h', pct: 42.85 },
    { text: '+1.5h', pct: 57.14 },
    { text: '+2h', pct: 71.42 },
    { text: '+2.5h', pct: 85.71 },
    { text: '+3h', pct: 100 }
  ];

  scaleEl.innerHTML = '';
  ticks.forEach(t => {
    const div = document.createElement('div');
    div.className = 'scale-tick' + (t.isNow ? ' now-tick' : '');
    div.style.left = `${t.pct}%`;
    div.textContent = t.text;
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

  // 1. Collect and calculate position percentage for all valid bosses
  const markerItems = [];
  Object.values(bossStates).forEach(boss => {
    let targetTimeMs = null;

    if (boss.next_spawn_time) {
      targetTimeMs = new Date(boss.next_spawn_time).getTime();
    } else if (boss.last_death_time) {
      targetTimeMs = new Date(boss.last_death_time).getTime();
    }

    if (!targetTimeMs || isNaN(targetTimeMs)) return;

    if (targetTimeMs >= windowStartMs && targetTimeMs <= windowEndMs) {
      const pct = ((targetTimeMs - windowStartMs) / totalWindowMs) * 100;
      const diffSec = Math.floor((targetTimeMs - nowMs) / 1000);
      markerItems.push({ boss, targetTimeMs, pct, diffSec });
    }
  });

  // Sort by position percentage ascending
  markerItems.sort((a, b) => a.pct - b.pct);

  // 2. Assign vertical tier (0, 1, 2) to adjacent close markers to prevent label overlap!
  let currentTier = 0;
  let prevPct = -999;

  markerItems.forEach(item => {
    if (item.pct - prevPct < 8) { // If within 8% width of previous pin
      currentTier = (currentTier + 1) % 3;
    } else {
      currentTier = 0;
    }
    prevPct = item.pct;
    item.tier = currentTier;
  });

  // 3. Render markers with vertical tier classes
  markerItems.forEach(item => {
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

    const timeStr = new Date(item.targetTimeMs).toTimeString().substring(0, 5);
    marker.innerHTML = `
      <div class="marker-content">
        <div class="marker-dot"></div>
        <div class="marker-label">${item.boss.name} ${timeStr}</div>
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
    if (!boss.next_spawn_time) return;
    const spawnMs = new Date(boss.next_spawn_time).getTime();
    if (isNaN(spawnMs)) return;

    const diffSec = Math.floor((spawnMs - nowMs) / 1000);
    // Include upcoming bosses in next 3 hours
    if (diffSec >= -300 && diffSec <= 3 * 3600) {
      upcomingBosses.push({ boss, spawnMs, diffSec });
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

    const timeStr = new Date(item.spawnMs).toTimeString().substring(0, 5);
    let diffStr = '已重生';
    if (item.diffSec > 0) {
      const m = Math.floor(item.diffSec / 60);
      diffStr = `剩 ${m} 分`;
    }

    card.innerHTML = `
      <span class="seq-idx">#${index + 1}</span>
      <span class="seq-name">👹 ${item.boss.name}</span>
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
    if (!boss.next_spawn_time) return;

    const spawnMs = new Date(boss.next_spawn_time).getTime();
    if (isNaN(spawnMs)) return;

    const diffSec = Math.floor((spawnMs - nowMs) / 1000);

    // Trigger warning when BOSS is between 1s and 300s (5 minutes) away
    if (diffSec > 0 && diffSec <= 300) {
      const spawnKey = `${boss.name}_${boss.next_spawn_time}`;
      if (!notifiedSpawns.has(spawnKey)) {
        notifiedSpawns.add(spawnKey);
        triggerBoss5MinWarning(boss, diffSec);
      }
    }
  });
}

function sendNativeNotification(title, body, tag = null) {
  if (!('Notification' in window)) return;

  const iconUrl = new URL('icons/icon-192.png', window.location.href).href;
  const options = {
    body: body,
    icon: iconUrl,
    badge: iconUrl,
    tag: tag || ('boss_notify_' + Date.now()),
    requireInteraction: true, // Forces Windows 10/11 Action Center toast to pop up and stay
    silent: false
  };

  // 1. Try Direct Notification API (Instant Windows Toast)
  try {
    const n = new Notification(title, options);
    n.onclick = () => { window.focus(); };
  } catch (e) {
    console.log("Direct Notification API error:", e);
  }

  // 2. Try ServiceWorker Registration showNotification fallback
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification(title, options).catch(err => console.log("SW showNotification error:", err));
    });
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

function triggerBoss5MinWarning(boss, secondsLeft) {
  const minsLeft = Math.ceil(secondsLeft / 60);
  const spawnTimeStr = new Date(boss.next_spawn_time).toTimeString().substring(0, 5);
  const title = `🔔 [BOSS 預警] ${boss.name}`;
  const body = `即將在 ${minsLeft} 分鐘後 (${spawnTimeStr}) 出現！請血盟成員準備！`;

  // Trigger Windows Native Toast / PWA Notification if enabled
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
    const statusEl = card.querySelector('.boss-status-label');
    if (!timerEl) return;

    if (boss.next_spawn_time) {
      const spawnMs = new Date(boss.next_spawn_time).getTime();
      const diffSec = Math.floor((spawnMs - nowMs) / 1000);

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
        if (statusEl) statusEl.textContent = '已重生';
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
      if (!b.next_spawn_time) return false;
      const diffMs = new Date(b.next_spawn_time).getTime() - nowMs;
      return diffMs > 0 && diffMs <= 30 * 60 * 1000;
    });
  } else if (currentBossFilter === 'alive') {
    filtered = bosses.filter(b => b.status === 'alive' || (b.next_spawn_time && new Date(b.next_spawn_time).getTime() <= nowMs));
  }

  // Sort by next_spawn_time ascending
  filtered.sort((a, b) => {
    const tA = a.next_spawn_time ? new Date(a.next_spawn_time).getTime() : Infinity;
    const tB = b.next_spawn_time ? new Date(b.next_spawn_time).getTime() : Infinity;
    return tA - tB;
  });

  grid.innerHTML = '';
  filtered.forEach(boss => {
    const card = document.createElement('div');
    const stateClass = `state-${boss.status || 'unknown'}`;
    card.className = `boss-card ${stateClass}`;
    card.dataset.bossName = boss.name;

    const lastDeathStr = boss.last_death_time ? new Date(boss.last_death_time).toTimeString().substring(0, 5) : '--:--';
    const nextSpawnStr = boss.next_spawn_time ? new Date(boss.next_spawn_time).toTimeString().substring(0, 5) : '--:--';
    const statusText = boss.status === 'alive' ? '已出現' : (boss.status === 'dead' ? '倒數中' : '未知');

    card.innerHTML = `
      <div class="boss-info">
        <span class="boss-name">👹 ${boss.name}</span>
        <span class="boss-status-label">${statusText}</span>
      </div>
      <div class="boss-timer-container">
        <div class="countdown-text">--:--</div>
      </div>
      <div class="boss-time-details">
        <div class="time-row"><span>預計重生：</span><strong>${nextSpawnStr}</strong></div>
        <div class="time-row"><span>上次死亡：</span><span>${lastDeathStr} (${boss.reported_by || '系統'})</span></div>
      </div>
      <button class="btn btn-secondary btn-full report-btn" onclick="openReportModal('${boss.name}')">
        ⚔️ 手動通報王死
      </button>
    `;
    grid.appendChild(card);
  });
}

/* ==========================================================================
   MANUAL REPORT MODAL & EVENT LISTENERS
   ========================================================================== */

function openReportModal(bossName) {
  selectedBossForReport = bossName;
  document.getElementById('reportBossName').textContent = `通報王怪：${bossName}`;

  // Default to "now" radio option
  const nowRadio = document.querySelector('input[name="timeType"][value="now"]');
  if (nowRadio) nowRadio.checked = true;
  
  const customGroup = document.getElementById('customTimeGroup');
  if (customGroup) customGroup.style.display = 'none';

  // Pre-fill time input with current HH:MM
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const customInput = document.getElementById('customTime');
  if (customInput) customInput.value = `${hh}:${mm}`;

  showModal('reportModal');
}

function setupUIEventListeners() {
  // Radio button toggle for time type in manual report modal
  document.querySelectorAll('input[name="timeType"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      const customGroup = document.getElementById('customTimeGroup');
      if (customGroup) {
        if (e.target.value === 'custom') {
          customGroup.style.display = 'flex';
          const now = new Date();
          const hh = String(now.getHours()).padStart(2, '0');
          const mm = String(now.getMinutes()).padStart(2, '0');
          const customInput = document.getElementById('customTime');
          if (customInput && !customInput.value) {
            customInput.value = `${hh}:${mm}`;
          }
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
  let eventTimeIso = new Date().toISOString();

  if (timeType === 'custom') {
    const customVal = document.getElementById('customTime')?.value;
    if (customVal) {
      const parts = customVal.split(':');
      const d = new Date();
      d.setHours(parseInt(parts[0]), parseInt(parts[1]), 0, 0);
      eventTimeIso = d.toISOString();
    }
  }

  const reportId = 'rep_' + Date.now();
  const reportData = {
    boss_name: selectedBossForReport,
    reported_by: reporterName,
    passcode: currentPasscode,
    timestamp: eventTimeIso,
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
