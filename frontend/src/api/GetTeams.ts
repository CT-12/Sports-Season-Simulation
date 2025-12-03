// MLB 球隊名稱到 ID 的映射表
const MLB_TEAM_IDS: Record<string, number> = {
    'Arizona Diamondbacks': 109,
    'Atlanta Braves': 144,
    'Athletics': 133,  // 資料庫中是 "Athletics"
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

const TEAM_LIST_URL: string = '/api/teams/'
const TEAM_RANKING_URL: string = '/api/team_ranking/'

async function fetchTeamsFromTeamsEndpoint(): Promise<Team[] | null> {
    try {
        const res = await fetch(TEAM_LIST_URL)
        if (!res.ok) return null
        const contentType = res.headers.get('content-type') || ''
        if (!contentType.includes('application/json')) return null
        const data = await res.json()
        const teams: Team[] = Array.isArray(data) ? data : (data.teams || [])
        
        // 為每個球隊添加 logo URL
        const teamsWithLogos = teams.map(team => ({
            ...team,
            logoUrl: `https://www.mlbstatic.com/team-logos/${team.id}.svg`
        }))
        
        return teamsWithLogos
    } catch (e) {
        console.debug('[GetTeams] teams endpoint failed:', e)
        return null
    }
}

async function fetchTeamsFromRankingEndpoint(): Promise<Team[]> {
    try {
        // 只需要獲取一次來取得球隊列表
        const res = await fetch(TEAM_RANKING_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ method: 'Pythagorean' })
        });
        
        if (!res.ok) {
            const txt = await res.text()
            console.error('[GetTeams] team_ranking POST failed:', res.status, txt)
            return []
        }
        
        const data = await res.json()
        
        // 後端返回格式: { "AL": ["team1", "team2", ...], "NL": [...] }
        const al: string[] = Array.isArray(data.AL) ? data.AL : []
        const nl: string[] = Array.isArray(data.NL) ? data.NL : []
        const names = [...al, ...nl]
        const unique = Array.from(new Set(names))
        
        // 使用 MLB 官方 team ID 映射表
        const teams: Team[] = unique.map((name) => {
            const mlbId = MLB_TEAM_IDS[name] || 1
            
            return {
                id: mlbId,
                name,
                logoUrl: `https://www.mlbstatic.com/team-logos/${mlbId}.svg`
            }
        })
        
        return teams
    } catch (e) {
        console.error('[GetTeams] fetch from ranking endpoint error:', e)
        return []
    }
}

async function getTeams(): Promise<Team[]> {
    // 先嘗試 /api/teams/
    const fromTeams = await fetchTeamsFromTeamsEndpoint()
    if (fromTeams && fromTeams.length > 0) {
        console.debug('[GetTeams] loaded from /api/teams/ count:', fromTeams.length)
        return fromTeams
    }
    // 若 /api/teams/ 不存在或回傳不正確，退回 /api/team_ranking/
    const fromRanking = await fetchTeamsFromRankingEndpoint()
    console.debug('[GetTeams] loaded from /api/team_ranking/ count:', fromRanking.length)
    return fromRanking
}
export default getTeams
// ...existing code...