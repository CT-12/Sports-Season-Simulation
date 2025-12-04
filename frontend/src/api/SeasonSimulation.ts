const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface TeamSeasonResult {
  team: string;
  wins: number;
  losses: number;
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
export async function runSeasonSimulation(method: string = 'Pythagorean'): Promise<SeasonSimulationResult | null> {
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
    // 後端已經根據預測勝率排序，排名越前的球隊預期勝率越高
    
    // 為每個球隊計算合理的勝場數
    // 第一名約 100 勝，最後一名約 60 勝
    const calculateWins = (rank: number, totalTeams: number): number => {
      // 使用非線性分布，讓前幾名差距較小，後面差距較大
      const maxWins = 102;
      const minWins = 58;
      const range = maxWins - minWins;
      
      // 使用二次函數分布
      const normalizedRank = (rank - 1) / (totalTeams - 1); // 0 to 1
      const winsRatio = 1 - Math.pow(normalizedRank, 1.3); // 非線性
      
      return Math.round(minWins + range * winsRatio);
    };
    
    const nlTeams: TeamSeasonResult[] = (data.NL || []).map((teamName: string, index: number) => {
      const wins = calculateWins(index + 1, data.NL.length);
      return {
        team: teamName,
        wins: wins,
        losses: 162 - wins,
        rank: index + 1,
        logo: getTeamLogo(teamName)
      };
    });
    
    const alTeams: TeamSeasonResult[] = (data.AL || []).map((teamName: string, index: number) => {
      const wins = calculateWins(index + 1, data.AL.length);
      return {
        team: teamName,
        wins: wins,
        losses: 162 - wins,
        rank: index + 1,
        logo: getTeamLogo(teamName)
      };
    });
    
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
