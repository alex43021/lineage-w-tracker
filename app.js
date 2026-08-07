// Global State Variables
let db = null;
let firebaseApp = null;
let currentPasscode = "123456789";
let currentDbUrl = "https://wchat-6ea90-default-rtdb.asia-southeast1.firebasedatabase.app/";
const defaultBossRules = [
  {
    "cooldown_mins": 1440,
    "days": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ],
    "death_keywords": [
      "克特",
      "擊敗"
    ],
    "fixed_times": [
      "18:00"
    ],
    "name": "克特",
    "spawn_keywords": [
      "克特",
      "出現"
    ],
    "type": "fixed"
  },
  {
    "cooldown_mins": 10080,
    "days": [
      3
    ],
    "death_keywords": [
      "巨大飛龍",
      "擊敗"
    ],
    "fixed_times": [
      "19:00"
    ],
    "name": "巨大飛龍",
    "spawn_keywords": [
      "巨大飛龍",
      "出現"
    ],
    "type": "fixed"
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "屠殺者莫利提亞被淨化而消失了。"
    ],
    "name": "屠殺者莫利提亞",
    "spawn_keywords": [
      "屠殺者莫利提亞開始尋找目標。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "殺戮者在死亡廢墟遭到討伐了"
    ],
    "name": "殺戮者",
    "spawn_keywords": [
      "殺戮者在死亡廢墟徘徊"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "龍牙兵的鬥士失去力量，然後消失了。"
    ],
    "name": "奧杜亞",
    "spawn_keywords": [
      "龍牙兵的鬥士在古魯丁地監徘徊。"
    ]
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "審判者拉馬修陷入了長久的睡眠。"
    ],
    "name": "審判者拉馬修",
    "spawn_keywords": [
      "解除了審判者拉馬修的長久封印。"
    ]
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "阿吐巴的大咒術師逃走了。"
    ],
    "name": "奈克偌斯",
    "spawn_keywords": [
      "阿吐巴的大咒術師出面狩獵奴隸了。"
    ]
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "那魯加的冠軍撤退了。"
    ],
    "name": "烏勒庫斯",
    "spawn_keywords": [
      "那魯加的冠軍出現在戰場上。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "卡司特的頭目逃到地洞裡去了。"
    ],
    "name": "卡司特王",
    "spawn_keywords": [
      "飢餓的頭目在卡司特群落出現了。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "波若斯的斥後隊長潰逃了。"
    ],
    "name": "尼羅德",
    "spawn_keywords": [
      "波若斯的斥侯隊長在要塞周圍徘徊。"
    ]
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "紅月失去力量消失了。"
    ],
    "name": "庫爾託",
    "spawn_keywords": [
      "悲哀森林上方升起了紅月。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "古老海賊王的憤怒漸漸消失了。"
    ],
    "name": "乾渴的德雷克",
    "spawn_keywords": [
      "古老海賊王的憤怒正對覬覦寶物的人們開始蠢蠢欲動。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "黑虎恰姆帕瓦特失去力量而死亡了。"
    ],
    "name": "黑虎恰姆帕瓦特",
    "spawn_keywords": [
      "響徹恰姆帕瓦特的咆哮聲。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "巨大怪獸相約下一次而回去了"
    ],
    "name": "史前巨鱷",
    "spawn_keywords": [
      "傳來巨大怪獸的咆哮聲"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "亡靈的追蹤者，在亞丁城堡地下監獄失去了蹤影。"
    ],
    "name": "黑蛇騎士團長麥肯",
    "spawn_keywords": [
      "亡靈的追蹤者，正在亞丁城堡地下監獄徘徊。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "巴爾博薩夫人相約下一次而消失了。"
    ],
    "name": "巴爾博薩夫人",
    "spawn_keywords": [
      "巴爾博薩夫人開始準備豐盛的晚餐。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "蜥蜴王落敗了。"
    ],
    "name": "卡爾迪修",
    "spawn_keywords": [
      "蜥蜴王正在等待挑戰。"
    ]
  },
  {
    "cooldown_mins": 240,
    "death_keywords": [
      "雪碧守衛往高雪壁隱藏了蹤跡。"
    ],
    "name": "大腳瑪幽",
    "spawn_keywords": [
      "雪碧守衛從深深的冬眠中甦醒了。"
    ]
  },
  {
    "cooldown_mins": 720,
    "death_keywords": [
      "巨大的兩個影子籠罩在巨人峽谷。"
    ],
    "name": "啃咬山峰的烏爾森",
    "spawn_keywords": [
      "巨大的兩個影子籠罩在巨人峽谷。"
    ]
  },
  {
    "cooldown_mins": 720,
    "death_keywords": [
      "巨大的兩個影子籠罩在巨人峽谷。"
    ],
    "name": "吞噬岩石的戈爾森",
    "spawn_keywords": [
      "巨大的兩個影子籠罩在巨人峽谷。"
    ]
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "埃柏特家族的飼養師頭目逃到了山寨。"
    ],
    "name": "頭目哈格瑪",
    "spawn_keywords": [
      "埃柏特家族的飼養師頭目出現於山寨。"
    ]
  },
  {
    "cooldown_mins": 240,
    "name": "飛龍1"
  },
  {
    "cooldown_mins": 240,
    "name": "飛龍2"
  },
  {
    "cooldown_mins": 240,
    "name": "飛龍3"
  },
  {
    "cooldown_mins": 240,
    "name": "飛龍4"
  },
  {
    "cooldown_mins": 480,
    "death_keywords": [
      "魔物招喚師的計畫失敗，然後返回異界了。"
    ],
    "name": "克洛林"
  },
  {
    "cooldown_mins": 120,
    "days": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ],
    "fixed_times": [
      "12:00",
      "23:00"
    ],
    "name": "風精靈王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "12:00",
      "23:00"
    ],
    "name": "地精靈王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "12:00",
      "23:00"
    ],
    "name": "火精靈王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "12:00",
      "23:00"
    ],
    "name": "水精靈王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5
    ],
    "fixed_times": [
      "15:00"
    ],
    "name": "巨蟻女皇",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:15"
    ],
    "name": "阿勒尼亞",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:10"
    ],
    "name": "克特",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:10"
    ],
    "name": "扭曲的傑尼斯女王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:10"
    ],
    "name": "不幸的幻象眼魔",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:15"
    ],
    "name": "恐怖的吸血鬼",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:10"
    ],
    "name": "巫師",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:15"
    ],
    "name": "死亡的殭屍王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:20"
    ],
    "name": "地獄的黑豹",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:20"
    ],
    "name": "不死的木乃伊王",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:10"
    ],
    "name": "阿爾斯卡利亞",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:15"
    ],
    "name": "殘酷的艾莉絲",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:15"
    ],
    "name": "黑暗的騎士范德",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:15"
    ],
    "name": "不滅的巫妖",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "黑色亡靈萊奧斯",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      0,
      1,
      2,
      3,
      4,
      5,
      6
    ],
    "fixed_times": [
      "20:00"
    ],
    "name": "傲慢的烏格奴斯",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "鑽石高崙",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      2
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "船長卡利索",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      6
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "狂風的夏斯奇",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      3
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "疾風的巨大飛龍",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      2,
      4,
      6
    ],
    "fixed_times": [
      "18:20"
    ],
    "name": "塔坤",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "18:20"
    ],
    "name": "自警團長馬托爾",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      3,
      5,
      0
    ],
    "fixed_times": [
      "18:20"
    ],
    "name": "不死鳥",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      3
    ],
    "fixed_times": [
      "15:00"
    ],
    "name": "死亡",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      2,
      4
    ],
    "fixed_times": [
      "15:00"
    ],
    "name": "古拉",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      5
    ],
    "fixed_times": [
      "15:00"
    ],
    "name": "墮落",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      5
    ],
    "fixed_times": [
      "15:00"
    ],
    "name": "惡魔",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "死亡騎士",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      0
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "漆黑的死亡騎士",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      4
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "巨大蜈蚣",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      5
    ],
    "fixed_times": [
      "19:20"
    ],
    "name": "大黑長者",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2
    ],
    "fixed_times": [
      "21:30"
    ],
    "name": "暗殺軍王史雷佛",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2
    ],
    "fixed_times": [
      "21:30"
    ],
    "name": "冥法軍王海露拜",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2
    ],
    "fixed_times": [
      "21:30"
    ],
    "name": "魔獸軍王巴蘭卡",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2
    ],
    "fixed_times": [
      "21:30"
    ],
    "name": "法令軍王蕾雅",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2
    ],
    "fixed_times": [
      "21:30"
    ],
    "name": "亡靈可利波斯",
    "type": "fixed"
  },
  {
    "cooldown_mins": 120,
    "days": [
      1,
      2,
      3,
      4,
      5,
      6,
      0
    ],
    "fixed_times": [
      "1:00",
      "3:00",
      "5:00",
      "7:00",
      "9:00",
      "11:00",
      "13:00",
      "15:00",
      "17:00",
      "19:00",
      "21:00",
      "23:00"
    ],
    "name": "萊茵哈德",
    "type": "fixed"
  }
];

let bossStates = {};
let bossRules = defaultBossRules;
let localTimers = {};
let notifiedSpawns = new Set(); // Prevent duplicate 5-minute notifications for the same spawn
let notifyEnabled = false;
let currentBossFilter = "all";
let selectedBossForReport = null;
let deferredPrompt = null;
let timelineSpanHours = parseInt(localStorage.getItem('lw_timeline_span') || "3", 10);
let showCooldownBosses = localStorage.getItem('lw_show_cooldown') !== 'false';
let showFixedBosses = localStorage.getItem('lw_show_fixed') !== 'false';
let appCheckSiteKey = (localStorage.getItem('lw_appcheck_site_key') || "").trim();
let isAppCheckDebugMode = localStorage.getItem('lw_appcheck_debug') === 'true';
let firebaseApiKey = (localStorage.getItem('lw_firebase_api_key') || "AIzaSyCICtzptbLc7mpqAkf4Vt7mBoNxSax9zMg").trim();

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
document.addEventListener('DOMContentLoaded', async () => {
  setupUIEventListeners();
  postLoadInit();
  await loadConfig();
});

function postLoadInit() {
  updateBossTypeToggleUI();
  setTimelineSpanHours(timelineSpanHours);
  
  // 1. Render boss grid & timeline immediately with default rules for zero-delay usability
  bossRules = defaultBossRules;
  initDefaultBossStates();
  renderBossGrid();
  updateTimeline();
  renderSequenceQueue();
  updateAppCheckBadge(false);

  // 2. Check localStorage overrides synchronously
  const savedUrl = localStorage.getItem('lw_db_url');
  const savedCode = localStorage.getItem('lw_passcode');
  if (savedUrl) currentDbUrl = savedUrl.replace(/\/$/, "");
  if (savedCode) currentPasscode = savedCode;

  // 3. Start 1-second interval timer for live countdowns & timeline indicator
  setInterval(tickRealtimeLoop, 1000);

  // 4. Initialize Firebase connection
  initFirebase(currentDbUrl, currentPasscode);
}

async function loadConfig() {
  try {
    const response = await fetch('data/firebase_config.json');
    if (response.ok) {
      const config = await response.json();
      let changed = false;
      if (config.databaseURL && config.databaseURL.replace(/\/$/, "") !== currentDbUrl) {
        currentDbUrl = config.databaseURL.replace(/\/$/, "");
        changed = true;
      }
      if (config.passcode && config.passcode !== currentPasscode) {
        currentPasscode = config.passcode;
        changed = true;
      }
      if (config.apiKey && typeof config.apiKey === 'string' && config.apiKey.trim()) {
        const newApiKey = config.apiKey.trim();
        if (newApiKey !== firebaseApiKey) {
          firebaseApiKey = newApiKey;
          localStorage.setItem('lw_firebase_api_key', firebaseApiKey);
          changed = true;
        }
      }
      if (config.appCheckSiteKey && typeof config.appCheckSiteKey === 'string' && config.appCheckSiteKey.trim()) {
        const newKey = config.appCheckSiteKey.trim();
        if (newKey !== appCheckSiteKey) {
          appCheckSiteKey = newKey;
          localStorage.setItem('lw_appcheck_site_key', appCheckSiteKey);
          changed = true;
        }
      }
      if (changed) {
        initFirebase(currentDbUrl, currentPasscode);
      }
    }
  } catch (e) {
    console.log("data/firebase_config.json not found, using defaults.");
  }
}

function normalizeBossStates(data) {
  if (!data || typeof data !== 'object') return {};
  const clean = {};
  Object.keys(data).forEach(k => {
    let key = k;
    try {
      if (k.includes('%')) {
        key = decodeURIComponent(k);
      }
    } catch(e) {}
    clean[key] = data[k];
    clean[key].name = key;
  });
  return clean;
}

// Automatically recover missing boss spawn times from historical /reports if DB was ever wiped
async function recoverBossStatesFromReportHistory() {
  try {
    const cleanUrl = currentDbUrl.replace(/\/$/, "");
    const reportsUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/reports.json`;
    const res = await fetch(reportsUrl);
    if (!res.ok) return;

    const reports = await res.json();
    if (!reports || typeof reports !== 'object') return;

    const latestReports = {};
    Object.values(reports).forEach(rep => {
      if (!rep || !rep.boss_name || !rep.timestamp) return;
      const bName = rep.boss_name;
      const repMs = parseIsoToEpochMs(rep.timestamp);
      if (!repMs) return;

      if (!latestReports[bName] || repMs > latestReports[bName].ms) {
        latestReports[bName] = { rep, ms: repMs };
      }
    });

    let recoveredAny = false;
    const patchPayload = {};

    Object.keys(latestReports).forEach(bName => {
      const { rep, ms } = latestReports[bName];
      const deathDate = new Date(ms);
      
      const currentSt = bossStates[bName];
      // If boss has no valid next_spawn_time or if timestamps are missing
      if (!currentSt || !currentSt.next_spawn_time) {
        const cooldownMins = getBossCooldownMins(bName);
        const nextSpawnDate = new Date(ms + cooldownMins * 60 * 1000);
        
        const pad = (n) => String(n).padStart(2, '0');
        const formatIso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

        if (!bossStates[bName]) bossStates[bName] = { name: bName };
        bossStates[bName].status = 'dead';
        bossStates[bName].last_death_time = formatIso(deathDate);
        bossStates[bName].next_spawn_time = formatIso(nextSpawnDate);
        bossStates[bName].reported_by = rep.reported_by || '歷史紀錄';
        bossStates[bName].is_overdue = false;
        bossStates[bName].source = 'report_recovery';

        patchPayload[bName] = bossStates[bName];
        recoveredAny = true;
      }
    });

    if (recoveredAny) {
      console.log("Successfully recovered missing boss states from report history!");
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();

      // Persist recovered states back to Firebase DB so all devices get them
      const stateUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/boss_states.json`;
      fetch(stateUrl, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patchPayload)
      }).catch(e => {});
    }
  } catch (e) {
    console.error("Report history recovery failed:", e);
  }
}

// Direct REST API Fallback Fetch for Instant Rendering
async function fetchDirectRestData(url, passcode) {
  try {
    const cleanUrl = url.replace(/\/$/, "");

    let authQuery = "";
    try {
      if (firebase.auth && firebase.auth(firebaseApp).currentUser) {
        const token = await firebase.auth(firebaseApp).currentUser.getIdToken();
        if (token) authQuery = `?auth=${token}`;
      }
    } catch(e) {}

    // 0. Fetch App Check config synced from desktop app
    const appCheckUrl = `${cleanUrl}/lineage_w_tracker/${passcode}/app_check_config.json${authQuery}`;
    try {
      const appCheckRes = await fetch(appCheckUrl);
      if (appCheckRes.ok) {
        const appCheckData = await appCheckRes.json();
        if (appCheckData && appCheckData.siteKey) {
          const fetchedKey = appCheckData.siteKey.trim();
          if (fetchedKey && fetchedKey !== appCheckSiteKey) {
            appCheckSiteKey = fetchedKey;
            localStorage.setItem('lw_appcheck_site_key', appCheckSiteKey);
          }
        }
      }
    } catch(e) {}

    // 1. Fetch remote boss rules
    const rulesUrl = `${cleanUrl}/lineage_w_tracker/${passcode}/boss_rules.json${authQuery}`;
    try {
      const rulesRes = await fetch(rulesUrl);
      if (rulesRes.ok) {
        const rulesData = await rulesRes.json();
        const normRules = normalizeBossRules(rulesData);
        if (normRules.length > 0) {
          bossRules = normRules;
          console.log("Successfully fetched remote boss_rules via REST:", bossRules);
        }
      }
    } catch(e) {
      console.log("REST boss_rules fetch failed:", e);
    }

    // 2. Fetch remote boss states
    const restUrl = `${cleanUrl}/lineage_w_tracker/${passcode}/boss_states.json${authQuery}`;
    const res = await fetch(restUrl);
    if (res.ok) {
      const data = await res.json();
      if (data && typeof data === 'object') {
        bossStates = normalizeBossStates(data);
        updateConnectionStatus('online');
        renderBossGrid();
        updateTimeline();
        renderSequenceQueue();
        recoverBossStatesFromReportHistory();
      } else {
        recoverBossStatesFromReportHistory();
      }
    } else {
      console.warn("REST boss_states HTTP status:", res.status);
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();
    }
  } catch (e) {
    console.log("REST fallback fetch failed:", e);
    renderBossGrid();
    updateTimeline();
    renderSequenceQueue();
  }
}

function normalizeBossRules(data) {
  if (!data) return defaultBossRules;
  let rules = [];
  if (Array.isArray(data)) {
    rules = data.filter(Boolean);
  } else if (typeof data === 'object') {
    rules = Object.values(data).filter(Boolean);
  }
  return rules.length > 0 ? rules : defaultBossRules;
}

// Initialize Firebase Realtime Database with Anonymous Authentication
async function initFirebase(url, passcode) {
  currentDbUrl = url.replace(/\/$/, "");
  currentPasscode = passcode || "123456789";

  updateConnectionStatus('connecting');

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

    firebaseApp = firebase.initializeApp({ databaseURL: currentDbUrl, apiKey: firebaseApiKey || "AIzaSyDHKGjbIMXam31tguYnm0ppJZ9fL7YDWBM", projectId: "lineage-w-boss-tracker" }, "LW-Tracker-" + Date.now());

    // 1. Activate App Check BEFORE database instance if siteKey exists (prevents Enforce Mode deadlock)
    if (appCheckSiteKey || isAppCheckDebugMode) {
      try {
        initAppCheck();
      } catch (appCheckErr) {
        console.warn("App Check activation notice:", appCheckErr.message);
      }
    } else {
      updateAppCheckBadge(false);
    }

    // 2. Firebase Anonymous Authentication
    try {
      const userCredential = await firebase.auth(firebaseApp).signInAnonymously();
      console.log("Firebase 匿名登入成功, uid:", userCredential.user.uid);
    } catch (authErr) {
      console.warn("Firebase 匿名登入失敗 (將以未認證模式繼續):", authErr.message);
    }

    // 3. Direct REST fetch after auth
    fetchDirectRestData(currentDbUrl, currentPasscode);

    // 4. Monitor auth state changes
    firebase.auth(firebaseApp).onAuthStateChanged((user) => {
      if (user) {
        console.log("Firebase Auth 已認證, uid:", user.uid, "isAnonymous:", user.isAnonymous);
      } else {
        console.log("Firebase Auth 使用者已登出");
      }
    });

    // 5. Create Realtime Database instance
    db = firebaseApp.database();

    // 6. Start realtime sync listeners
    startSyncListeners();

    // 7. Monitor socket connection status
    db.ref('.info/connected').on('value', (snap) => {
      if (snap.val() === true) {
        updateAppCheckBadge(true);
        updateConnectionStatus('online');
        localStorage.setItem('lw_db_url', currentDbUrl);
        localStorage.setItem('lw_passcode', currentPasscode);
        if (appCheckSiteKey || isAppCheckDebugMode) {
          updateAppCheckBadge(true);
        }
      }
    });
  } catch (e) {
    console.error("Firebase init failed:", e);
  }
}

function initAppCheck() {
  if (!firebaseApp || typeof firebase.appCheck !== 'function') return;

  if (!appCheckSiteKey && !isAppCheckDebugMode) {
    updateAppCheckBadge(false);
    return;
  }

  try {
    if (isAppCheckDebugMode) {
      self.FIREBASE_APPCHECK_DEBUG_TOKEN = true;
      console.log("Firebase App Check Debug Token enabled.");
    }

    const appCheck = firebase.appCheck(firebaseApp);
    if (appCheckSiteKey) {
      try {
        appCheck.activate(
          new firebase.appCheck.ReCaptchaV3Provider(appCheckSiteKey),
          false // Set auto-refresh to false to prevent invalid domain errors from dropping WebSocket
        );
        console.log("Firebase App Check reCAPTCHA v3 activated for:", appCheckSiteKey);
        updateAppCheckBadge(true);
      } catch (actErr) {
        console.warn("App Check activate note:", actErr.message);
        updateAppCheckBadge(false);
      }
    } else if (isAppCheckDebugMode) {
      try {
        appCheck.activate(
          new firebase.appCheck.CustomProvider({
            getToken: () => Promise.resolve({ token: "DEBUG_TOKEN", expireTimeMillis: Date.now() + 3600000 })
          }),
          false
        );
        updateAppCheckBadge(true, "Debug");
      } catch (actErr) {
        updateAppCheckBadge(false);
      }
    }
  } catch (e) {
    console.warn("Firebase App Check note:", e.message);
    updateAppCheckBadge(false);
  }
}

function updateAppCheckBadge(enabled, label = "") {
  const btn = document.getElementById('appCheckBtn');
  const text = document.getElementById('appCheckStatusText');
  const bannerText = document.getElementById('appCheckBannerText');
  const banner = document.getElementById('appCheckStatusBanner');

  if (btn && text) {
    if (enabled) {
      btn.classList.add('active');
      text.textContent = label ? `🛡️ ${label}` : '防護:開';
    } else {
      btn.classList.remove('active');
      text.textContent = 'App Check';
    }
  }

  if (bannerText && banner) {
    if (enabled) {
      banner.style.background = 'rgba(16, 185, 129, 0.15)';
      banner.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      bannerText.style.color = '#6ee7b7';
      bannerText.textContent = label ? `防護狀態：已啟用 (${label} 測試模式)` : '防護狀態：🟢 已從雲端/桌面端自動同步金鑰並啟用防護！';
    } else {
      banner.style.background = 'rgba(239, 68, 68, 0.15)';
      banner.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      bannerText.style.color = '#fca5a5';
      bannerText.textContent = '防護狀態：🔴 未啟用 (請輸入 Key 或在桌面端點擊儲存同步)';
    }
  }
}

// Start realtime sync listeners for boss_states
function startSyncListeners() {
  if (!db) return;

  // 1. Sync BOSS States
  db.ref(`lineage_w_tracker/${currentPasscode}/boss_states`).on('value', (snapshot) => {
    const data = snapshot.val();
    if (data && typeof data === 'object') {
      bossStates = normalizeBossStates(data);
      updateConnectionStatus('online');
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();
      recoverBossStatesFromReportHistory();
    } else {
      recoverBossStatesFromReportHistory();
    }
  });

  // 2. Sync BOSS Rules
  db.ref(`lineage_w_tracker/${currentPasscode}/boss_rules`).on('value', (snapshot) => {
    const data = snapshot.val();
    const normRules = normalizeBossRules(data);
    if (normRules.length > 0) {
      bossRules = normRules;
      renderBossGrid();
      updateTimeline();
      renderSequenceQueue();
    }
  });

  // 3. Realtime Sync App Check Config
  db.ref(`lineage_w_tracker/${currentPasscode}/app_check_config`).on('value', (snapshot) => {
    const data = snapshot.val();
    if (data && data.siteKey) {
      const fetchedKey = data.siteKey.trim();
      if (fetchedKey && fetchedKey !== appCheckSiteKey) {
        console.log("Realtime App Check config updated from Firebase:", fetchedKey);
        appCheckSiteKey = fetchedKey;
        localStorage.setItem('lw_appcheck_site_key', appCheckSiteKey);
        initFirebase(currentDbUrl, currentPasscode);
      } else if (fetchedKey) {
        updateAppCheckBadge(true);
      }
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
  // 1. Priority 1: Active synced bossRules array
  if (Array.isArray(bossRules) && bossRules.length > 0) {
    const rule = bossRules.find(r => r.name === bossName);
    if (rule && rule.cooldown_mins) {
      return parseInt(rule.cooldown_mins, 10);
    }
  }
  // 2. Priority 2: State-level cooldown_mins
  if (bossStates[bossName] && bossStates[bossName].cooldown_mins) {
    return parseInt(bossStates[bossName].cooldown_mins, 10);
  }
  // 3. Priority 3: Fallback lookup in default rules array
  if (Array.isArray(defaultBossRules)) {
    const defRule = defaultBossRules.find(r => r.name === bossName);
    if (defRule && defRule.cooldown_mins) {
      return parseInt(defRule.cooldown_mins, 10);
    }
  }
  return 60;
}

function calculateNextFixedSpawnMs(rule, nowMs = Date.now()) {
  if (!rule) return null;

  let fixedTimesList = [];
  if (Array.isArray(rule.fixed_times)) {
    fixedTimesList = rule.fixed_times;
  } else if (typeof rule.fixed_times === 'string') {
    fixedTimesList = rule.fixed_times.split(',').map(t => t.trim()).filter(Boolean);
  }
  if (fixedTimesList.length === 0) return null;

  const now = new Date(nowMs);
  let validDays = [0, 1, 2, 3, 4, 5, 6];
  if (Array.isArray(rule.days) && rule.days.length > 0) {
    validDays = rule.days.map(Number);
  }

  let minCandidateMs = null;

  for (let dayOffset = 0; dayOffset <= 8; dayOffset++) {
    const candidateDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() + dayOffset);
    const dayOfWeek = candidateDate.getDay(); // 0 = Sun, 1 = Mon, ..., 6 = Sat

    if (!validDays.includes(dayOfWeek)) continue;

    for (const timeStr of fixedTimesList) {
      const parts = String(timeStr).trim().split(':');
      if (parts.length < 2) continue;
      const hh = parseInt(parts[0], 10);
      const mm = parseInt(parts[1], 10);
      if (isNaN(hh) || isNaN(mm)) continue;

      const candidateMs = new Date(candidateDate.getFullYear(), candidateDate.getMonth(), candidateDate.getDate(), hh, mm, 0, 0).getTime();

      if (candidateMs > nowMs) {
        if (minCandidateMs === null || candidateMs < minCandidateMs) {
          minCandidateMs = candidateMs;
        }
      }
    }
  }
  return minCandidateMs;
}

function getEffectiveBossState(boss, nowMs = Date.now()) {
  let isOverdue = false;
  let displayName = boss.name;

  const cooldownMins = getBossCooldownMins(boss.name);
  const cooldownMs = cooldownMins * 60 * 1000;

  const bossRule = bossRules.find(r => r.name === boss.name);
  const isFixed = (bossRule && bossRule.type === 'fixed') || (boss.type === 'fixed');

  let spawnMs = null;

  if (boss.status === 'alive') {
    isOverdue = false;
    spawnMs = parseIsoToEpochMs(boss.last_spawn_time) || nowMs;
  } else if (isFixed && bossRule) {
    isOverdue = false;
    spawnMs = calculateNextFixedSpawnMs(bossRule, nowMs);
    if (!spawnMs) {
      spawnMs = parseIsoToEpochMs(boss.next_spawn_time);
    }
  } else {
    const deathMs = parseIsoToEpochMs(boss.last_death_time);
    if (deathMs && !isNaN(deathMs)) {
      spawnMs = deathMs + cooldownMs;
    } else {
      spawnMs = parseIsoToEpochMs(boss.next_spawn_time);
    }

    if (spawnMs && !isNaN(spawnMs)) {
      if (spawnMs <= nowMs) {
        isOverdue = true;
        while (spawnMs <= nowMs) {
          spawnMs += cooldownMs;
        }
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
    isOverdue,
    isFixed
  };
}

/* ==========================================================================
   DYNAMIC INTERACTIVE TIMELINE SYSTEM (-30m ~ NOW ~ +3h)
   Completing ALL boss events in the 3.5-hour range (-30m ~ +3h) with 3-tier staggering!
   ========================================================================== */

function setTimelineSpanHours(spanVal) {
  timelineSpanHours = (spanVal === 1) ? 1 : 3;
  localStorage.setItem('lw_timeline_span', timelineSpanHours);

  document.querySelectorAll('[data-span]').forEach(b => {
    b.classList.toggle('active', parseInt(b.dataset.span, 10) === timelineSpanHours);
  });

  const subtitle = document.getElementById('timelineSubtitle');
  if (subtitle) {
    subtitle.textContent = (timelineSpanHours === 1) ? '(-30m ~ 目前 ~ +1h)' : '(-30m ~ 目前 ~ +3h)';
  }

  updateTimeline();
  setTimeout(centerTimelineNow, 50);
}

function updateTimelineScale(nowMs = Date.now()) {
  const scaleEl = document.getElementById('timelineScale');
  if (!scaleEl) return;

  let ticks = [];
  if (timelineSpanHours === 1) {
    // 1-Hour View: Total 90 mins (-30m to +60m). NOW at 33.333%
    ticks = [
      { offsetMins: -30, pct: 0 },
      { offsetMins: -15, pct: 16.666 },
      { offsetMins: 0, pct: 33.333, isNow: true },
      { offsetMins: 15, pct: 50.0 },
      { offsetMins: 30, pct: 66.666 },
      { offsetMins: 45, pct: 83.333 },
      { offsetMins: 60, pct: 100 }
    ];
  } else {
    // 3-Hour View: Total 210 mins (-30m to +180m). NOW at 14.2857%
    ticks = [
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
  }

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

function initDefaultBossStates() {
  if (Array.isArray(defaultBossRules)) {
    defaultBossRules.forEach(rule => {
      if (rule.name && !bossStates[rule.name]) {
        bossStates[rule.name] = {
          name: rule.name,
          type: rule.type || 'cooldown',
          status: 'unknown',
          last_spawn_time: null,
          last_death_time: null,
          next_spawn_time: null,
          cooldown_mins: rule.cooldown_mins || 240,
          days: rule.days || [0,1,2,3,4,5,6],
          fixed_times: rule.fixed_times || ["18:00"],
          source: 'fixed_schedule',
          reported_by: 'system'
        };
      }
    });
  }
}

function updateBossTypeToggleUI() {
  const btnCd = document.getElementById('btnToggleCooldown');
  const btnFixed = document.getElementById('btnToggleFixed');
  const isCd = (typeof showCooldownBosses !== 'undefined') ? showCooldownBosses : true;
  const isFixed = (typeof showFixedBosses !== 'undefined') ? showFixedBosses : true;
  if (btnCd) btnCd.classList.toggle('active', isCd);
  if (btnFixed) btnFixed.classList.toggle('active', isFixed);
}

function getActiveBosses() {
  // Ensure every boss rule in bossRules has a state entry in bossStates
  if (Array.isArray(bossRules)) {
    bossRules.forEach(rule => {
      if (rule.name && !bossStates[rule.name]) {
        bossStates[rule.name] = {
          name: rule.name,
          type: rule.type || 'cooldown',
          status: 'unknown',
          last_spawn_time: null,
          last_death_time: null,
          next_spawn_time: null,
          source: 'fixed_schedule',
          reported_by: 'system'
        };
      }
    });
  }

  const allBosses = Object.values(bossStates);
  let activeList = allBosses;

  if (Array.isArray(bossRules) && bossRules.length > 0) {
    const validNames = new Set(bossRules.map(r => r.name));
    activeList = activeList.filter(b => validNames.has(b.name));
  }

  return activeList.filter(b => {
    const bossRule = bossRules.find(r => r.name === b.name);
    const isFixed = (bossRule && bossRule.type === 'fixed') || (b.type === 'fixed');
    if (isFixed) {
      return (typeof showFixedBosses !== 'undefined') ? showFixedBosses : true;
    } else {
      return (typeof showCooldownBosses !== 'undefined') ? showCooldownBosses : true;
    }
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

  const rightSpanMins = (timelineSpanHours === 1) ? 60 : 180;
  const totalMins = 30 + rightSpanMins; // 90 mins or 210 mins

  // NOW position percentage (Always 30 mins from left!)
  const nowPct = (30 / totalMins) * 100;
  if (nowInd) {
    nowInd.style.left = `${nowPct}%`;
  }

  const windowStartMs = nowMs - (30 * 60 * 1000); // -30m
  const windowEndMs = nowMs + (rightSpanMins * 60 * 1000);  // +60m or +180m
  const totalWindowMs = totalMins * 60 * 1000;

  layer.innerHTML = '';

  const markerItems = [];

  // Evaluate EVERY active boss for past death events AND future spawn cycles in the 3.5h window!
  getActiveBosses().forEach(boss => {
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
          const isFixed = eff.isFixed;
          markerItems.push({
            boss,
            targetTimeMs: spawnMs,
            pct,
            diffSec,
            eventType: 'spawn',
            isFixed,
            displayText: `${isFixed ? '👑 ' : ''}${eff.displayName} ${formatLocalTime24(spawnMs)}`
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
    marker.className = `timeline-marker tier-${item.tier}${item.isFixed ? ' timeline-marker-fixed' : ''}`;
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

  getActiveBosses().forEach(boss => {
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
  getActiveBosses().forEach(boss => {
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

function sendNativeNotification(title, body, tag = null, autoCloseMs = null) {
  if (!('Notification' in window)) return;

  if (Notification.permission !== 'granted') {
    console.log("Notification permission not granted:", Notification.permission);
    return;
  }

  const iconUrl = new URL('icons/icon-192.png', window.location.href).href;
  const options = {
    body: body,
    icon: iconUrl,
    badge: iconUrl,
    tag: tag || ('boss_notify_' + Date.now()),
    requireInteraction: autoCloseMs ? false : true,
    silent: false,
    vibrate: [300, 100, 300, 100, 400],
    data: {
      url: window.location.href
    }
  };

  // On Mobile PWA (iOS Safari & Android Chrome), ALWAYS use navigator.serviceWorker.ready
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready.then(reg => {
      reg.showNotification(title, options).then(() => {
        if (autoCloseMs && reg.getNotifications) {
          setTimeout(() => {
            reg.getNotifications({ tag: options.tag }).then(notifications => {
              notifications.forEach(n => n.close());
            });
          }, autoCloseMs);
        }
      }).catch(err => {
        console.log("SW showNotification error, trying fallback:", err);
        createDirectNotification();
      });
    }).catch(err => {
      console.log("SW ready error:", err);
      createDirectNotification();
    });
  } else {
    createDirectNotification();
  }

  function createDirectNotification() {
    try {
      const n = new Notification(title, options);
      n.onclick = () => { window.focus(); };
      if (autoCloseMs) {
        setTimeout(() => {
          try { n.close(); } catch(e){}
        }, autoCloseMs);
      }
    } catch (e) {
      console.log("Direct Notification API error (expected on iOS):", e);
    }
  }
}

function requestAndTestNotification() {
  if (!('Notification' in window)) {
    alert("您的手機或瀏覽器不支援系統推播通知。");
    return;
  }

  if (Notification.permission === 'granted') {
    triggerTestNotification();
  } else if (Notification.permission === 'denied') {
    alert("【手機通知權限被停用】\n\n- iPhone 用戶：請至 iPhone「設定」➔「通知」➔ 找到「天堂W BOSS」標籤並開啟「允許通知」。\n\n- Android 用戶：請至 Chrome 網址鎖頭圖示 ➔ 選擇「允許通知」。");
  } else {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        triggerTestNotification();
      } else {
        alert("未授權通知權限。若想開啟，請點擊上方「🔔 預警」按鈕！");
      }
    });
  }
}

function triggerTestNotification() {
  const title = "🔔 [BOSS 預警] 通知功能測試成功！";
  const body = "當 BOSS 重生倒數剩餘 5 分鐘時，將會發送通知。此測試通知將於 8 秒後自動關閉。";
  
  sendNativeNotification(title, body, "test_notification", 8000);

  alert("🎉 已觸發測試推播！\n\n此測試通知將於 8 秒後自動關閉。\n若未收到，請確認 Windows【請勿打擾 / 專注輔助】與 Chrome 通知權限！");
}

function triggerBoss5MinWarning(boss, secondsLeft, spawnMs, displayName) {
  const minsLeft = Math.ceil(secondsLeft / 60);
  const spawnTimeStr = formatLocalTime24(spawnMs);
  const nameToUse = displayName || boss.name;
  const title = `🔔 [BOSS 預警] ${nameToUse}`;
  const body = `即將在 ${minsLeft} 分鐘後 (${spawnTimeStr}) 出現！王到時間後通知將自動關閉。`;

  // Auto-close notification exactly when boss spawn time arrives!
  const autoCloseMs = Math.max(5000, secondsLeft * 1000);

  if (notifyEnabled) {
    sendNativeNotification(title, body, boss.name, autoCloseMs);
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
        if (diffSec >= 3600) {
          const h = Math.floor(diffSec / 3600);
          const m = Math.floor((diffSec % 3600) / 60);
          const s = diffSec % 60;
          timerEl.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        } else {
          const m = Math.floor(diffSec / 60);
          const s = diffSec % 60;
          timerEl.textContent = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
        }

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

  const bosses = getActiveBosses();
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
    const isFixedBoss = eff.isFixed;
    card.className = `boss-card ${stateClass}${isFixedBoss ? ' fixed-schedule-card' : ''}`;
    card.dataset.bossName = boss.name;

    const lastDeathStr = boss.last_death_time ? formatLocalTime24(boss.last_death_time) : (eff.isOverdue && eff.spawnMs ? `${formatLocalTime24(eff.spawnMs - eff.cooldownMs)} (推算)` : '--:--');
    const nextSpawnStr = eff.spawnMs ? formatLocalTime24(eff.spawnMs) : '--:--';
    const statusText = boss.status === 'alive' ? '已出現' : (boss.status === 'dead' ? '倒數中' : (eff.isOverdue ? '倒數中(過)' : '未知'));

    const bossRule = bossRules.find(r => r.name === boss.name);
    let typeBadgeHtml = '';
    if (eff.isFixed && bossRule) {
      const days = bossRule.days || [];
      const dayLabels = ['日', '一', '二', '三', '四', '五', '六'];
      let dayText = '每日';
      if (days.length > 0 && days.length < 7) {
        dayText = '週' + days.map(d => dayLabels[d]).join('、');
      }
      const timesText = (bossRule.fixed_times || []).join(', ');
      typeBadgeHtml = `<span class="fixed-type-badge">📅 定時: ${dayText} ${timesText}</span>`;
    }

    let actionsHtml = '';
    if (eff.isFixed) {
      actionsHtml = `
        <button class="btn btn-quick-kill btn-fixed-kill" onclick="quickReportKillNow('${boss.name}')" style="width: 100%;" title="紀錄擊殺時間 (固定王不影響下次預計重生時間)">
          ⚔️ 紀錄擊殺
        </button>
      `;
    } else {
      actionsHtml = `
        <button class="btn btn-quick-kill" onclick="quickReportKillNow('${boss.name}')" title="一鍵通報剛剛擊殺 (現在時間)">
          ⚔️ 剛擊殺
        </button>
        <button class="btn btn-custom-time" onclick="openReportModal('${boss.name}')" title="指定歷史擊殺時間">
          🕒 指定時間
        </button>
      `;
    }

    card.innerHTML = `
      <div class="boss-info">
        <span class="boss-name">${isFixedBoss ? '👑' : '👹'} ${eff.displayName} ${typeBadgeHtml}</span>
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
        ${actionsHtml}
      </div>
    `;
    grid.appendChild(card);
  });
}

async function applyAndBroadcastBossDeath(bossName, deathDateObj, reporterName = '成員') {
  if (!bossName || !deathDateObj) return;

  const bossRule = bossRules.find(r => r.name === bossName);
  const isFixed = (bossRule && bossRule.type === 'fixed') || (bossStates[bossName] && bossStates[bossName].type === 'fixed');

  const deathMs = deathDateObj.getTime();
  let nextSpawnMs = null;

  if (isFixed) {
    // For fixed schedule bosses: death is purely a historical record and does NOT alter or shift the fixed schedule spawn time!
    nextSpawnMs = calculateNextFixedSpawnMs(bossRule, Date.now());
    if (!nextSpawnMs && bossStates[bossName] && bossStates[bossName].next_spawn_time) {
      nextSpawnMs = parseIsoToEpochMs(bossStates[bossName].next_spawn_time);
    }
  } else {
    const cooldownMins = getBossCooldownMins(bossName);
    nextSpawnMs = deathMs + (cooldownMins * 60 * 1000);
  }

  const nextSpawnDate = new Date(nextSpawnMs);

  const pad = (n) => String(n).padStart(2, '0');
  const formatIso = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;

  const lastDeathIso = formatIso(deathDateObj);
  const nextSpawnIso = formatIso(nextSpawnDate);

  // Update local state immediately for < 50ms instant UI response
  if (!bossStates[bossName]) {
    bossStates[bossName] = { name: bossName };
  }

  bossStates[bossName].status = 'dead';
  bossStates[bossName].last_death_time = lastDeathIso;
  bossStates[bossName].next_spawn_time = nextSpawnIso;
  bossStates[bossName].reported_by = reporterName;
  bossStates[bossName].is_overdue = false;
  bossStates[bossName].source = 'manual';

  // Render local UI right away
  renderBossGrid();
  updateTimeline();
  renderSequenceQueue();

  // 1. Primary: Update Firebase via active WebSocket database instance (automatic auth)
  if (db) {
    try {
      db.ref(`lineage_w_tracker/${currentPasscode}/boss_states/${bossName}`).update(bossStates[bossName]);
    } catch(e) {}
  }

  // 2. Secondary: Direct REST PATCH fallback with auth token
  let authQuery = "";
  try {
    if (firebase.auth && firebase.auth(firebaseApp).currentUser) {
      const token = await firebase.auth(firebaseApp).currentUser.getIdToken();
      if (token) authQuery = `?auth=${token}`;
    }
  } catch(e) {}

  const cleanUrl = currentDbUrl.replace(/\/$/, "");
  const stateUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/boss_states.json${authQuery}`;
  
  const updatePayload = {};
  updatePayload[bossName] = bossStates[bossName];

  fetch(stateUrl, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updatePayload)
  })
  .then(res => {
    if (res.ok) {
      console.log(`Successfully patched boss_states for ${bossName} directly in Firebase.`);
    }
  })
  .catch(err => console.error("Error updating boss_states:", err));

  // 3. Record in /reports/<reportId>.json for log history
  const reportId = 'rep_' + Date.now();
  const reportData = {
    boss_name: bossName,
    reported_by: reporterName,
    time_type: 'custom',
    custom_time: `${pad(deathDateObj.getHours())}:${pad(deathDateObj.getMinutes())}`,
    passcode: currentPasscode,
    timestamp: lastDeathIso,
    status: 'dead'
  };

  if (db) {
    try {
      db.ref(`lineage_w_tracker/${currentPasscode}/reports/${reportId}`).set(reportData);
    } catch(e) {}
  }

  const reportUrl = `${cleanUrl}/lineage_w_tracker/${currentPasscode}/reports/${reportId}.json${authQuery}`;
  fetch(reportUrl, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reportData)
  }).catch(e => {});
}

function quickReportKillNow(bossName) {
  if (!bossName) return;
  const now = new Date();
  const bossRule = bossRules.find(r => r.name === bossName);
  const isFixed = (bossRule && bossRule.type === 'fixed') || (bossStates[bossName] && bossStates[bossName].type === 'fixed');
  applyAndBroadcastBossDeath(bossName, now, '成員');
  if (isFixed) {
    alert(`🎉 已紀錄 ${bossName} 擊殺！(固定王計時維持預設排程不變)`);
  } else {
    alert(`🎉 已通報 ${bossName} 剛剛擊殺！預計重生時間已自動更新。`);
  }
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
  const bossRule = bossRules.find(r => r.name === bossName);
  if (bossRule && bossRule.type === 'fixed') {
    quickReportKillNow(bossName);
    return;
  }
  selectedBossForReport = bossName;
  document.getElementById('reportBossName').textContent = `指定擊殺時間：${bossName}`;

  const customRadio = document.querySelector('input[name="timeType"][value="custom"]');
  if (customRadio) customRadio.checked = true;
  
  const customGroup = document.getElementById('customTimeGroup');
  if (customGroup) customGroup.style.display = 'flex';

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
  const rightSpanMins = (timelineSpanHours === 1) ? 60 : 180;
  const nowPct = 30 / (30 + rightSpanMins);
  const nowPx = trackWidth * nowPct;
  const scrollPos = nowPx - (wrapperWidth / 2);

  wrapper.scrollTo({
    left: Math.max(0, scrollPos),
    behavior: 'smooth'
  });
}

function setupUIEventListeners() {
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

  // Boss Type Filter Toggles (週期王 / 定時王)
  document.getElementById('btnToggleCooldown')?.addEventListener('click', () => {
    showCooldownBosses = !showCooldownBosses;
    localStorage.setItem('lw_show_cooldown', showCooldownBosses);
    updateBossTypeToggleUI();
    updateTimeline();
    renderSequenceQueue();
    renderBossGrid();
  });

  document.getElementById('btnToggleFixed')?.addEventListener('click', () => {
    showFixedBosses = !showFixedBosses;
    localStorage.setItem('lw_show_fixed', showFixedBosses);
    updateBossTypeToggleUI();
    updateTimeline();
    renderSequenceQueue();
    renderBossGrid();
  });

  // Timeline Span Toggle Buttons (1h vs 3h)
  document.querySelectorAll('[data-span]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const spanVal = parseInt(e.currentTarget.dataset.span, 10);
      setTimelineSpanHours(spanVal);
    });
  });

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

  // Firebase App Check Modal Handlers (Read-only status view)
  document.getElementById('appCheckBtn')?.addEventListener('click', () => {
    updateAppCheckBadge(Boolean(appCheckSiteKey));
    showModal('appCheckModal');
  });

  document.getElementById('closeAppCheckBtn')?.addEventListener('click', () => hideModal('appCheckModal'));
  document.getElementById('confirmAppCheckBtn')?.addEventListener('click', () => hideModal('appCheckModal'));

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

  document.getElementById('notifyToggleBtn')?.addEventListener('click', (e) => {
    notifyEnabled = !notifyEnabled;
    const btn = e.currentTarget;
    btn.classList.toggle('active', notifyEnabled);
    btn.querySelector('.pill-text').textContent = notifyEnabled ? '5分鐘預警: 開啟' : '5分鐘預警: 關閉';

    if (notifyEnabled) {
      requestAndTestNotification();
    }
  });

  document.getElementById('testPushBtn')?.addEventListener('click', () => {
    requestAndTestNotification();
  });

  document.querySelectorAll('[data-boss-filter]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('[data-boss-filter]').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentBossFilter = e.target.dataset.bossFilter;
      renderBossGrid();
    });
  });

  document.getElementById('closeReportBtn')?.addEventListener('click', () => hideModal('reportModal'));
  document.getElementById('cancelReportBtn')?.addEventListener('click', () => hideModal('reportModal'));
  document.getElementById('submitReportBtn')?.addEventListener('click', submitManualReport);
}

function submitManualReport() {
  if (!selectedBossForReport) return;

  const reporterName = '成員';
  const d = new Date();

  const hh = document.getElementById('customHour')?.value || '00';
  const mm = document.getElementById('customMinute')?.value || '00';
  
  d.setHours(parseInt(hh, 10), parseInt(mm, 10), 0, 0);

  // If selected custom time is in the future relative to current time, assume it occurred yesterday
  const now = new Date();
  if (d.getTime() > now.getTime()) {
    d.setDate(d.getDate() - 1);
  }

  applyAndBroadcastBossDeath(selectedBossForReport, d, reporterName);
  hideModal('reportModal');
  alert(`🎉 成功通報 ${selectedBossForReport} 已擊殺！預計重生時間已自動更新。`);
}

function showModal(id) {
  document.getElementById(id)?.classList.add('show');
}
function hideModal(id) {
  document.getElementById(id)?.classList.remove('show');
}
