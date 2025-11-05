// script.js — 終極版 MLB 對戰模擬器
// 功能：載入隊伍清單 -> 選隊伍 A/B -> 載入名單 -> 可拖放互換 -> 依 rating 計算勝率
// 注意：若瀏覽器直接 fetch StatsAPI 發生 CORS，請用本地 server 或 proxy

const TEAM_LIST_URL = 'https://statsapi.mlb.com/api/v1/teams?sportId=1';
const ROSTER_URL = teamId => `https://statsapi.mlb.com/api/v1/teams/${teamId}/roster`;

const teamASelect = document.getElementById('teamASelect');
const teamBSelect = document.getElementById('teamBSelect');
const rosterAEl = document.getElementById('rosterA');
const rosterBEl = document.getElementById('rosterB');
const teamANameEl = document.getElementById('teamAName');
const teamBNameEl = document.getElementById('teamBName');
const teamAInfoEl = document.getElementById('teamAInfo');
const teamBInfoEl = document.getElementById('teamBInfo');
const winBarA = document.querySelector('#winBarA .fill');
const winBarB = document.querySelector('#winBarB .fill');
const winPctA = document.getElementById('winPctA');
const winPctB = document.getElementById('winPctB');
const resetBtn = document.getElementById('resetBtn');

// cache rosters & keep original copies for reset
const rosterCache = {};      // teamId -> players[]
const originalRosters = {};  // teamId -> deep copy

// store current selected team ids
let teamAId = null, teamBId = null;

// --- helper: deterministic pseudo-random rating based on id ---
// produce rating in [40, 100] (like a player rating)
function idToRating(id) {
  // simple hash -> deterministic
  let x = Number(id) || 0;
  // convert to string for some mixing
  const s = String(id) + 'mlbrating_v1';
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  // map to [40,100]
  const r = 40 + (h % 61); // 40..100
  return r;
}

// --- fetch team list ---
async function loadTeams() {
  try {
    const res = await fetch(TEAM_LIST_URL);
    if (!res.ok) throw new Error('teams fetch failed');
    const data = await res.json();
    const teams = data.teams || [];
    populateTeamSelects(teams);
  } catch (err) {
    console.error('載入隊伍清單失敗：', err);
    // fallback: minimal mock teams
    const mock = [
      {id:109, name:'Los Angeles Dodgers'},
      {id:147, name:'New York Yankees'},
      {id:117, name:'Houston Astros'},
      {id:144, name:'Atlanta Braves'}
    ];
    populateTeamSelects(mock);
  }
}

function populateTeamSelects(teams) {
  teamASelect.innerHTML = '<option value="">-- 選擇隊伍 A --</option>';
  teamBSelect.innerHTML = '<option value="">-- 選擇隊伍 B --</option>';
  teams.forEach(t => {
    const o1 = document.createElement('option');
    o1.value = t.id;
    o1.textContent = t.name;
    const o2 = o1.cloneNode(true);
    teamASelect.appendChild(o1);
    teamBSelect.appendChild(o2);
  });
}

// --- load roster for team ---
async function loadRoster(teamId, targetEl, side) {
  targetEl.innerHTML = '<div style="color:var(--muted)">載入中...</div>';
  try {
    if (rosterCache[teamId]) {
      // deep copy when rendering so dragging won't modify cache original
      const copy = rosterCache[teamId].map(p => ({...p}));
      originalRosters[side] = rosterCache[teamId].map(p => ({...p}));
      renderRoster(copy, targetEl);
      return;
    }
    const res = await fetch(ROSTER_URL(teamId));
    if (!res.ok) throw new Error('roster fetch failed');
    const data = await res.json();
    const players = (data.roster || []).map(item => {
      const pid = item.person?.id || Math.floor(Math.random()*1e6);
      return {
        id: pid,
        name: item.person?.fullName || 'Unknown',
        position: item.position?.abbreviation || '',
        rating: idToRating(pid)
      };
    });
    // cache original
    rosterCache[teamId] = players.map(p => ({...p}));
    originalRosters[side] = players.map(p => ({...p}));
    renderRoster(players, targetEl);
  } catch (err) {
    console.error('讀取名單失敗:', err);
    targetEl.innerHTML = '<div style="color:var(--muted)">讀取失敗或 CORS 問題</div>';
  }
}

// --- render roster to DOM ---
function renderRoster(players, containerEl) {
  containerEl.innerHTML = '';
  players.forEach(p => {
    const card = document.createElement('div');
    card.className = 'player-card';
    card.draggable = true;
    card.dataset.playerId = p.id;
    card.dataset.name = p.name;
    card.dataset.pos = p.position;
    card.dataset.rating = p.rating;
    card.innerHTML = `
      <div class="name">${escapeHtml(p.name)}</div>
      <div class="pos">${escapeHtml(p.position || '')}</div>
      <div class="rating">
        <div class="score">${p.rating}</div>
        <div class="bar"><div class="fill" style="width:${(p.rating-40)/60*100}%"></div></div>
      </div>
    `;
    // drag events
    card.addEventListener('dragstart', handleDragStart);
    card.addEventListener('dragend', handleDragEnd);
    containerEl.appendChild(card);
  });
  // attach drop listeners to both roster containers
  attachDropHandlers();
  updateTeamDisplays();
}

// --- drag/drop handling ---
let dragSrc = null;
function handleDragStart(e) {
  dragSrc = e.currentTarget;
  e.dataTransfer.setData('text/plain', JSON.stringify({
    id: e.currentTarget.dataset.playerId,
    name: e.currentTarget.dataset.name,
    rating: e.currentTarget.dataset.rating
  }));
  e.dataTransfer.effectAllowed = 'move';
  e.currentTarget.classList.add('dragging');
}
function handleDragEnd(e) {
  e.currentTarget.classList.remove('dragging');
}

function attachDropHandlers() {
  [rosterAEl, rosterBEl].forEach(container => {
    container.removeEventListener('dragover', onDragOver);
    container.removeEventListener('drop', onDrop);
    container.addEventListener('dragover', onDragOver);
    container.addEventListener('drop', onDrop);
  });
}
function onDragOver(e) {
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
}
function onDrop(e) {
  e.preventDefault();
  const payload = e.dataTransfer.getData('text/plain');
  if (!payload) return;
  const data = JSON.parse(payload);
  // find source card element (dragSrc)
  const targetList = e.currentTarget; // rosterAEl or rosterBEl
  // if dragging from same container and dropped inside, ignore
  if (dragSrc && dragSrc.parentElement === targetList) {
    // do nothing (or re-order if needed)
    return;
  }
  // remove from old parent and append to new
  if (dragSrc && dragSrc.parentElement) {
    targetList.appendChild(dragSrc);
    // update dataset rating values remain
    updateTeamDisplays();
  } else {
    // fallback: create a new card
    const newCard = document.createElement('div');
    newCard.className = 'player-card';
    newCard.draggable = true;
    newCard.dataset.playerId = data.id;
    newCard.dataset.name = data.name;
    newCard.dataset.rating = data.rating;
    newCard.innerHTML = `
      <div class="name">${escapeHtml(data.name)}</div>
      <div class="pos"></div>
      <div class="rating">
        <div class="score">${data.rating}</div>
        <div class="bar"><div class="fill" style="width:${(data.rating-40)/60*100}%"></div></div>
      </div>
    `;
    newCard.addEventListener('dragstart', handleDragStart);
    newCard.addEventListener('dragend', handleDragEnd);
    targetList.appendChild(newCard);
    updateTeamDisplays();
  }
}

// --- compute team ratings & win probabilities ---
function computeTeamStats(containerEl) {
  const cards = Array.from(containerEl.querySelectorAll('.player-card'));
  let total = 0;
  cards.forEach(c => {
    const r = Number(c.dataset.rating) || 60;
    total += r;
  });
  return {count: cards.length, total};
}

function updateTeamDisplays() {
  // team A
  const a = computeTeamStats(rosterAEl);
  const b = computeTeamStats(rosterBEl);
  const aName = teamASelect.options[teamASelect.selectedIndex]?.text || '隊伍 A';
  const bName = teamBSelect.options[teamBSelect.selectedIndex]?.text || '隊伍 B';
  teamANameEl.textContent = aName;
  teamBNameEl.textContent = bName;
  teamAInfoEl.textContent = `球員數：${a.count} · Rating：${Math.round(a.total)}`;
  teamBInfoEl.textContent = `球員數：${b.count} · Rating：${Math.round(b.total)}`;

  // compute win probability using Elo-like normalized function
  const epsilon = 1e-6;
  const totalBoth = a.total + b.total + epsilon;
  const probA = a.total / totalBoth;
  const probB = b.total / totalBoth;
  // update bars & percents
  const pctA = Math.round(probA*1000)/10;
  const pctB = Math.round(probB*1000)/10;
  winBarA.style.width = `${pctA}%`;
  winBarB.style.width = `${pctB}%`;
  winPctA.textContent = `${pctA}%`;
  winPctB.textContent = `${pctB}%`;
}

// --- utility: escape html for name display
function escapeHtml(s){ return String(s||'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

// --- event wiring for team selects ---
teamASelect.addEventListener('change', async () => {
  const id = teamASelect.value;
  teamAId = id || null;
  if (id) {
    await loadRoster(id, rosterAEl, 'A');
  } else {
    rosterAEl.innerHTML = '';
  }
  updateTeamDisplays();
});
teamBSelect.addEventListener('change', async () => {
  const id = teamBSelect.value;
  teamBId = id || null;
  if (id) {
    await loadRoster(id, rosterBEl, 'B');
  } else {
    rosterBEl.innerHTML = '';
  }
  updateTeamDisplays();
});

// reset to original rosters for current selected teams
resetBtn.addEventListener('click', () => {
  if (teamAId && originalRosters['A']) {
    renderRoster(originalRosters['A'].map(p => ({...p})), rosterAEl);
  }
  if (teamBId && originalRosters['B']) {
    renderRoster(originalRosters['B'].map(p => ({...p})), rosterBEl);
  }
  updateTeamDisplays();
});

// initial load
loadTeams().then(() => {
  // optionally select two default teams (like Dodgers + Yankees)
  // try to pick first two different options
  if (teamASelect.options.length > 1) teamASelect.selectedIndex = 1;
  if (teamBSelect.options.length > 2) teamBSelect.selectedIndex = 2;
  // trigger change to load rosters (wait a tick)
  setTimeout(()=> {
    teamASelect.dispatchEvent(new Event('change'));
    teamBSelect.dispatchEvent(new Event('change'));
  }, 200);
});

// recompute when user drops (listen globally for drop events inside rosters)
document.addEventListener('drop', () => setTimeout(updateTeamDisplays, 80));
document.addEventListener('dragend', () => setTimeout(updateTeamDisplays, 80));
