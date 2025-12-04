const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// 顯示用的指標對應（前端選擇 → 顯示在畫面上的值）
const DISPLAY_METRIC_MAP: Record<string, string> = {
  'ops': 'OPS',
  'h_war': 'WAR',
  'avg': 'AVG',
  'era': 'ERA',
  'p_war': 'WAR',
  'whip': 'WHIP',
};

// 計算用的指標對應（前端選擇 → 用於計算 Rating 的值）
const CALCULATION_METRIC_MAP: Record<string, string> = {
  'ops': 'OPS_plus',           // 顯示 OPS，計算用 OPS+
  'h_war': 'WAR',              // WAR 不變
  'avg': 'AVG_normalized',     // 顯示 AVG，計算用 AVG_normalized
  'era': 'ERA_plus',           // 顯示 ERA，計算用 ERA+
  'p_war': 'WAR',              // WAR 不變
  'whip': 'WHIP_normalized',   // 顯示 WHIP，計算用 WHIP_normalized
};

function getMetricValue(ratingObj: Record<string, any> | undefined, metricKey: string) {
  if (!ratingObj) return null;
  const fieldName = metricKey;
  const tryKeys = [fieldName, fieldName.toLowerCase(), fieldName.toUpperCase()];
  for (const k of tryKeys) {
    if (k in ratingObj && ratingObj[k] != null) return ratingObj[k];
  }
  return null;
}

function mapRawToPlayer(
  item: any,
  hitterMetric: string = 'ops',
  pitcherMetric: string = 'era'
) {
  const pid = item?.id ?? Math.floor(Math.random() * 1e6);
  const name = item?.name ?? 'Unknown';
  const position = item?.position ?? '';
  
  const isPitcher = position.toLowerCase().includes('pitcher') || position === 'P';
  const raw = item?.Rating ?? {};
  
  let displayValue = 0;  // 顯示的值
  let rating = 0;        // 計算用的值
  
  if (isPitcher) {
    // 投手：取得顯示值和計算值
    const displayField = DISPLAY_METRIC_MAP[pitcherMetric] || pitcherMetric.toUpperCase();
    const calculationField = CALCULATION_METRIC_MAP[pitcherMetric] || pitcherMetric.toUpperCase();
    
    const displayVal = getMetricValue(raw, displayField);
    const calcVal = getMetricValue(raw, calculationField);
    
    displayValue = displayVal != null ? Number(displayVal) : 0;
    rating = calcVal != null ? Number(calcVal) : 0;
  } else {
    // 打者：取得顯示值和計算值
    const displayField = DISPLAY_METRIC_MAP[hitterMetric] || hitterMetric.toUpperCase();
    const calculationField = CALCULATION_METRIC_MAP[hitterMetric] || hitterMetric.toUpperCase();
    
    const displayVal = getMetricValue(raw, displayField);
    const calcVal = getMetricValue(raw, calculationField);
    
    displayValue = displayVal != null ? Number(displayVal) : 0;
    rating = calcVal != null ? Number(calcVal) : 0;
  }
  
  return { 
    id: pid, 
    name, 
    position, 
    rating,           // 用於計算 Rating
    displayValue      // 用於顯示
  };
}

async function getRoster(
  teamId: number | string,
  teamName?: string,
  hitterMetric: string = 'ops_plus',
  pitcherMetric: string = 'p_war'
): Promise<any[]> {
  if (!teamName) {
    console.warn('[GetRoster] teamName is required');
    return [];
  }

  console.debug('[GetRoster] teamName=', teamName, 'hitterMetric=', hitterMetric, 'pitcherMetric=', pitcherMetric);
  
  try {
    const url = `${API_BASE}/matchup/`;
    const payload = {
      team_A: teamName,
      team_B: teamName,
      method: 'Pythagorean'
    };
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!res.ok) {
      const text = await res.text();
      console.error('[GetRoster] backend error', res.status, text?.slice(0, 500));
      return [];
    }
    
    const text = await res.text();
    const ct = res.headers.get('content-type') || '';
    if (!ct.includes('application/json')) {
      console.error('[GetRoster] unexpected content-type', ct);
      return [];
    }
    
    const data = text ? JSON.parse(text) : {};
    const raw = Array.isArray(data.team_A) ? data.team_A : [];
    
    if (raw && raw.length > 0) {
      const players = raw.map((item: any) => mapRawToPlayer(item, hitterMetric, pitcherMetric));
      console.debug('[GetRoster] loaded', players.length, 'players');
      return players;
    }
    
    return [];
    
  } catch (e) {
    console.error('[GetRoster] error:', e);
    return [];
  }
}

export default getRoster;