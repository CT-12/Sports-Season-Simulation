# 🏈 MLB 對戰模擬器 - 開發日誌

## 📅 日期：2025年12月2日

---

## 🎯 專案目標

建立一個 MLB 對戰模擬器，支援兩種模式：
1. **Team 模式**：使用 Pythagorean 或 Elo 方法計算球隊勝率（後端 Monte Carlo 模擬 10,000 次）
2. **Player 模式**：基於球員統計數據計算勝率，支援球員拖曳調整

---

## 🔧 已完成功能清單

### ✅ 核心功能
1. **Team/Player 模式切換**：使用 UISlider 在兩種模式間切換
2. **球隊選擇**：從 30 支 MLB 球隊中選擇兩支進行對戰
3. **球隊 Logo 顯示**：正確顯示每支球隊的官方 Logo（多層容錯機制）
4. **球員名單載入**：自動載入選中球隊的球員名單
5. **勝率計算**：
   - Team 模式：後端 API + Monte Carlo 模擬
   - Player 模式：前端即時計算
6. **統計指標選擇**：
   - 打者：OPS+、WAR、wRC+
   - 投手：WAR、ERA、WHIP
7. **動態分數顯示**：
   - Team 模式：顯示 Pythagorean/Elo 分數
   - Player 模式：顯示球員數量和 Rating
8. **球員拖曳功能**（Player 模式）：拖曳球員調整陣容並即時更新勝率
9. **Reset功能**：讓球員回到初始球隊
10. **開始模擬功能**：讓交易之後開始做ELo或畢氏期望模擬


---

## 📡 API 架構

### 後端 API 端點

#### 1. `/api/team_ranking/` - 獲取球隊排名
**Request:**
```bash
POST /api/team_ranking/
Content-Type: application/json

{
  "method": "Pythagorean"  # 或 "Elo"
}
```

**Response:**
```json
{
  "NL": ["Milwaukee Brewers", "Chicago Cubs", ...],
  "AL": ["New York Yankees", "Boston Red Sox", ...]
}
```

#### 2. `/api/matchup/` - 分析對戰
**Request:**
```bash
POST /api/matchup/
Content-Type: application/json

{
  "team_A": "Los Angeles Dodgers",
  "team_B": "New York Yankees",
  "method": "Pythagorean"  # 或 "Elo"
}
```

**Response:**
```json
{
  "team_A": [...球員陣容...],
  "team_B": [...球員陣容...],
  "team_A_score": 65.23,
  "team_B_score": 58.47,
  "team_A_win_prob": 63.45,
  "team_B_win_prob": 36.55
}
```

#### 3. `/api/roster/` - 獲取球員名單
**Request:**
```bash
GET /api/roster/?teamId=119&teamName=Los Angeles Dodgers&hitterStat=ops_plus&pitcherStat=p_war
```

**Response:**
```json
[
  {
    "id": 660271,
    "name": "Shohei Ohtani",
    "position": "DH",
    "rating": 95.5,
    "Rating": {
      "AVG": 0.304,
      "OPS": 1.036,
      "ERA": null,
      "WHIP": null
    }
  },
  ...
]
```

---

## 🗂️ 前端架構

### 核心組件

```
App.tsx (主應用)
├── Header
│   └── UISlider (Team/Player 切換)
├── SelectionMenu (選擇統計指標)
│   ├── Team 模式: Pythagorean / Elo
│   └── Player 模式: 打者指標 / 投手指標
├── TeamSelect (選擇球隊)
│   └── Modal 彈窗顯示 30 支球隊
└── Arena (對戰區域)
    ├── TeamPanel (左側球隊)
    │   ├── 球隊名稱
    │   ├── 分數/Rating
    │   ├── 勝率條
    │   └── PlayerCard List (球員卡片)
    └── TeamPanel (右側球隊)
```

### 主要 Hooks

#### `useTeamManager.ts`
- 管理球隊選擇和球員名單
- 處理球員拖曳移動
- 管理統計指標選擇

#### `useTeamSelect.ts`
- 管理球隊選擇 Modal
- 追蹤已選擇的球隊
- 確認選擇並呼叫回調

---

## 🎨 UI/UX 特色

### 球隊選擇介面
- **卡片式設計**：160px x 200px 卡片
- **球隊 Logo**：96x96 圖片，完整顯示不裁切
- **選擇狀態**：藍色邊框 + 背景高亮
- **多層容錯**：圖片載入失敗自動嘗試 4 種來源
  1. `team-logos` 官方 Logo
  2. `team-cap-on-light` 帽子 Logo
  3. ESPN Logo
  4. Midfield Logo

### 球員卡片
- **動態指標顯示**：根據選擇的統計指標顯示對應數值
- **斜體標籤**：顯示當前使用的指標（如 "OPS+"）
- **拖曳功能**（Player 模式）：可拖曳球員調整陣容
- **位置顯示**：清楚標示球員位置

### 勝率顯示
- **視覺化進度條**：動態寬度顯示勝率
- **百分比數值**：精確到小數點後一位
- **即時更新**：模式切換或陣容調整時自動更新

---

## 🔢 勝率計算邏輯

### Team 模式 - 後端 Monte Carlo 模擬

#### Pythagorean 方法
1. 取得 2025 年球隊數據（得分/失分）
2. 計算 Pythagorean 勝率
3. 應用回歸到平均值（70% 實際數據 + 30% 平均值）
4. **Monte Carlo 模擬 10,000 次**
   - 從常態分佈抽樣分數
   - 標準差基於比賽場次
   - 計算勝場數
5. 返回勝率百分比

```python
MC_SIMULATIONS = 10000
team_a_wins = 0

for _ in range(MC_SIMULATIONS):
    score_a = np.random.normal(base_score_a, std_dev_a)
    score_b = np.random.normal(base_score_b, std_dev_b)
    
    if score_a > score_b:
        team_a_wins += 1

team_a_win_prob = (team_a_wins / MC_SIMULATIONS) * 100
```

#### Elo 方法
1. 從資料庫查詢最新 Elo rating
2. 應用季節回歸預測 2026 年
   - `rating_2026 = (rating_2025 * 0.75) + (1500 * 0.25)`
3. 轉換為 0-100 分數
4. 使用 Elo 公式計算勝率

### Player 模式 - 前端簡單計算

```typescript
const ratingA = sum(playerA.rating)
const ratingB = sum(playerB.rating)
const probA = ratingA / (ratingA + ratingB) * 100
const probB = 100 - probA
```

---

## 📊 資料流

### Team 模式
```
使用者選擇球隊 A、B
    ↓
切換 Pythagorean/Elo
    ↓
App.tsx useEffect 觸發
    ↓
呼叫 analyzeMatchup(teamA, teamB, method)
    ↓
後端計算勝率 (Monte Carlo 10,000 次)
    ↓
返回 team_A_win_prob, team_B_win_prob
    ↓
更新 teamModeWinProb state
    ↓
Arena 顯示勝率
```

### Player 模式
```
使用者選擇球隊 A、B
    ↓
獲取球員名單 (getRoster)
    ↓
使用者拖曳球員調整陣容
    ↓
computeWinProbability(rosterA, rosterB)
    ↓
計算: probA = ratingA / (ratingA + ratingB)
    ↓
Arena 顯示勝率
```

---

## 🗄️ 資料庫結構

### 核心資料表

```sql
-- 球隊基本資料
CREATE TABLE teams (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    abbreviation VARCHAR(10),
    league VARCHAR(2),  -- AL/NL
    division VARCHAR(50)
);

-- 球員基本資料
CREATE TABLE players (
    player_id INT PRIMARY KEY,
    player_name VARCHAR(100),
    current_team_id INT,
    position_name VARCHAR(20),
    position_type VARCHAR(20),
    season INT
);

-- 打者數據
CREATE TABLE player_hitting_stats (
    id SERIAL PRIMARY KEY,
    player_id INT,
    season INT,
    avg DECIMAL(5,3),
    ops DECIMAL(5,3),
    ops_plus INT,
    h_war DECIMAL(5,2),
    wrc_plus INT,
    hr INT,
    rbi INT
);

-- 投手數據
CREATE TABLE player_pitching_stats (
    id SERIAL PRIMARY KEY,
    player_id INT,
    season INT,
    era DECIMAL(5,2),
    whip DECIMAL(5,3),
    p_war DECIMAL(5,2),
    so INT,
    w INT,
    l INT
);

-- 球隊 Elo 歷史記錄
CREATE TABLE team_elo_history (
    id SERIAL PRIMARY KEY,
    team_id INT,
    season INT,
    date DATE,
    rating DECIMAL(10,2),
    UNIQUE(team_id, season, date)
);
```

---

## 🔧 MLB Team ID 映射表

```typescript
const MLB_TEAM_IDS: Record<string, number> = {
    'Arizona Diamondbacks': 109,
    'Atlanta Braves': 144,
    'Baltimore Orioles': 110,
    'Boston Red Sox': 111,
    'Chicago Cubs': 112,
    'Chicago White Sox': 145,
    'Cincinnati Reds': 113,
    'Cleveland Guardians': 114,
    'Colorado Rockies': 115,
    'Detroit Tigers': 116,
    'Houston Astros': 117,
    'Kansas City Royals': 118,
    'Los Angeles Angels': 108,
    'Los Angeles Dodgers': 119,
    'Miami Marlins': 146,
    'Milwaukee Brewers': 158,
    'Minnesota Twins': 142,
    'New York Mets': 121,
    'New York Yankees': 147,
    'Oakland Athletics': 133,
    'Philadelphia Phillies': 143,
    'Pittsburgh Pirates': 134,
    'San Diego Padres': 135,
    'San Francisco Giants': 137,
    'Seattle Mariners': 136,
    'St. Louis Cardinals': 138,
    'Tampa Bay Rays': 139,
    'Texas Rangers': 140,
    'Toronto Blue Jays': 141,
    'Washington Nationals': 120
};
```

---

## 🚀 啟動專案

### 後端
```bash
cd backend
python manage.py runserver 0.0.0.0:8000
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

### 訪問
- **前端**: http://localhost:5173 (或其他可用端口)
- **後端 API**: http://localhost:8000/api/

---

## 🐛 常見問題排查

### 球隊圖片不顯示
1. 檢查 `MLB_TEAM_IDS` 映射表是否包含該球隊
2. 查看 Console 的錯誤訊息
3. 確認球隊名稱完全匹配（包括大小寫）
4. 多層容錯機制會自動嘗試備用來源

### 勝率顯示 50/50
1. 確認已選擇兩支球隊
2. 確認後端服務正在運行
3. 檢查 Console 是否有 API 錯誤
4. 確認資料庫中有相關數據

### 無法選擇球隊
1. 確認後端 `/api/team_ranking/` 正常返回
2. 檢查 teams 陣列是否正確載入
3. 查看 Console 的錯誤訊息

### 球員名單空白
1. 確認後端 `/api/roster/` 正常返回
2. 確認 teamId 和 teamName 正確
3. 確認資料庫中有該球隊的球員數據

---

## ✨ 技術棧

### 前端
- **React** 18.2
- **TypeScript** 5.2
- **Vite** 5.0
- **CSS Modules**

### 後端
- **Django** 5.0
- **Django REST Framework** 3.14
- **PostgreSQL / MySQL**
- **NumPy** (Monte Carlo 模擬)

---

## 📝 重要修改記錄

### 2025/12/2 - 完成的功能
1. ✅ Pythagorean/Elo 按鈕切換
2. ✅ 球隊圖片載入（多層容錯）
3. ✅ Team 模式顯示球隊分數
4. ✅ Team/Player 模式勝率計算
5. ✅ 球員卡片動態指標顯示
6. ✅ Team 模式也顯示球員名單
7. ✅ 球隊選擇功能正常運作


