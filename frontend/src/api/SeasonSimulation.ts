const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface TeamSeasonResult {
  team: string;
  rank: number;
  logo?: string;
}

export interface SeasonSimulationResult {
  NL: TeamSeasonResult[];
  AL: TeamSeasonResult[];
}

/**
 * 執行蒙地卡羅賽季模擬
 */
export async function runTeamModeSeasonSimulation(method: string = 'Pythagorean'): Promise<SeasonSimulationResult | null> {
  /*
  這是用來進行隊伍層級的賽季模擬的函式。 它會呼叫後端 API，傳送所選的模擬方法（Pythagorean 或 Elo），
  並接收模擬結果，包含國聯和美聯各隊的排名。
  然後將結果轉換成 SeasonSimulationResult 格式並回傳。
  如果發生錯誤，則回傳 null。
  */
  try {
    console.log('[SeasonSimulation] Starting simulation with method:', method);
    
    const url = `${API_BASE}/team_ranking/`;
    const payload = {
      method: method === 'pythagorean' ? 'Pythagorean' : 'Elo'
    };
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    
    if (!res.ok) {
      const text = await res.text();
      console.error('[SeasonSimulation] backend error', res.status, text?.slice(0, 500));
      return null;
    }
    
    const data = await res.json();
    console.log('[SeasonSimulation] Received data:', data);
    
    // 後端返回的格式: { "NL": ["team1", "team2", ...], "AL": [...] }
    // 後端已經根據模擬結果排序，直接使用排名
    
    const nlTeams: TeamSeasonResult[] = (data.NL || []).map((teamName: string, index: number) => ({
      team: teamName,
      rank: index + 1,
      logo: getTeamLogo(teamName)
    }));
    
    const alTeams: TeamSeasonResult[] = (data.AL || []).map((teamName: string, index: number) => ({
      team: teamName,
      rank: index + 1,
      logo: getTeamLogo(teamName)
    }));
    
    return { NL: nlTeams, AL: alTeams };
    
  } catch (e) {
    console.error('[SeasonSimulation] error:', e);
    return null;
  }
}

export async function runPlayerModeSeasonSimulation(hitterMetric: string, pitcherMetric: string, transactions: Transaction[], setTransactions: React.Dispatch<React.SetStateAction<Transaction[]>>): Promise<SeasonSimulationResult | null> {
  try {
    console.log('[SeasonSimulation] Starting player mode simulation with hitterMetric:', hitterMetric, 'and pitcherMetric:', pitcherMetric);
    let url = '';
    let payload = {};

    if (transactions.length) {

      url = `${API_BASE}/simulation/ranking/`;
      payload = {
          hitter_metric: hitterMetric,
          pitcher_metric: pitcherMetric,
          season: "2025",
          transactions: transactions
      };

    } else {
      url = `${API_BASE}/ranking/`;
      payload = {
          hitter_metric: hitterMetric,
          pitcher_metric: pitcherMetric
      };
    }

    
    
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const text = await res.text();
      console.error('[SeasonSimulation] backend error', res.status, text?.slice(0, 500));
      return null;
    }
    
    const data = await res.json();
    console.log('[SeasonSimulation] Received data:', data);
    const NL_ranking = data.NL.map((item: [string, number]) => item[0]); // item = [teamName, score]
    const AL_ranking = data.AL.map((item: [string, number]) => item[0]);
    
    const nlTeams: TeamSeasonResult[] = (NL_ranking || []).map((teamName: string, index: number) => ({
      team: teamName,
      rank: index + 1,
      logo: getTeamLogo(teamName)
    }));
    
    const alTeams: TeamSeasonResult[] = (AL_ranking || []).map((teamName: string, index: number) => ({
      team: teamName,
      rank: index + 1,
      logo: getTeamLogo(teamName)
    }));
    
    // Clear transactions after simulation
    setTransactions([]);

    return { NL: nlTeams, AL: alTeams };
    
  } catch (e) {
    console.error('[SeasonSimulation] error:', e);
    return null;
  }
}

/**
 * 獲取球隊 logo URL
 */
function getTeamLogo(teamName: string): string {
  // 使用 ESPN 的球隊 logo API
  const teamIdMap: Record<string, string> = {
    'Arizona Diamondbacks': 'ari',
    'Atlanta Braves': 'atl',
    'Baltimore Orioles': 'bal',
    'Boston Red Sox': 'bos',
    'Chicago Cubs': 'chc',
    'Chicago White Sox': 'chw',
    'Cincinnati Reds': 'cin',
    'Cleveland Guardians': 'cle',
    'Colorado Rockies': 'col',
    'Detroit Tigers': 'det',
    'Houston Astros': 'hou',
    'Kansas City Royals': 'kc',
    'Los Angeles Angels': 'laa',
    'Los Angeles Dodgers': 'lad',
    'Miami Marlins': 'mia',
    'Milwaukee Brewers': 'mil',
    'Minnesota Twins': 'min',
    'New York Mets': 'nym',
    'New York Yankees': 'nyy',
    'Athletics': 'oak',
    'Philadelphia Phillies': 'phi',
    'Pittsburgh Pirates': 'pit',
    'San Diego Padres': 'sd',
    'San Francisco Giants': 'sf',
    'Seattle Mariners': 'sea',
    'St. Louis Cardinals': 'stl',
    'Tampa Bay Rays': 'tb',
    'Texas Rangers': 'tex',
    'Toronto Blue Jays': 'tor',
    'Washington Nationals': 'wsh',
  };
  
  const teamId = teamIdMap[teamName] || 'mlb';
  return `https://a.espncdn.com/i/teamlogos/mlb/500/${teamId}.png`;
}
