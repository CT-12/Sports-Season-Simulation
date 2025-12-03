const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

// 指標名稱對應表（SelectionMenu 的 value → 後端 Rating 欄位名）
const METRIC_MAP: Record<string, string> = {
  'ops_plus': 'OPS',      // fallback 用 OPS（後端可能沒有 OPS+）
  'h_war': 'WAR',
  'wrc_plus': 'OPS',      // fallback 用 OPS
  'p_war': 'WAR',
  'era': 'ERA',
  'whip': 'WHIP',
};

function getMetricValue(ratingObj: Record<string, any> | undefined, metricKey: string) {
  if (!ratingObj) return null;
  const fieldName = METRIC_MAP[metricKey] || metricKey.toUpperCase();
  const tryKeys = [fieldName, fieldName.toLowerCase(), fieldName.toUpperCase()];
  for (const k of tryKeys) {
    if (k in ratingObj && ratingObj[k] != null) return ratingObj[k];
  }
  return null;
}

function mapRawToPlayer(
  item: any,
  hitterMetric: string = 'ops_plus',
  pitcherMetric: string = 'p_war'
) {
  const pid = item?.id ?? Math.floor(Math.random() * 1e6);
  const name = item?.name ?? 'Unknown';
  const position = item?.position ?? '';
  
  const isPitcher = position.toLowerCase().includes('pitcher') || position === 'P';
  const raw = item?.Rating ?? {};
  
  let rating = 0;
  
  if (isPitcher) {
    const val = getMetricValue(raw, pitcherMetric);
    rating = val != null ? Number(val) : 0;
  } else {
    const val = getMetricValue(raw, hitterMetric);
    rating = val != null ? Number(val) : 0;
  }
  
  return { id: pid, name, position, rating };
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
      const players = raw.map(item => mapRawToPlayer(item, hitterMetric, pitcherMetric));
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