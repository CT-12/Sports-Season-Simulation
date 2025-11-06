const ROSTER_URL = (teamId: string) => `https://statsapi.mlb.com/api/v1/teams/${teamId}/roster`;

function idToRating(id: number) {
    const s = String(id) + 'mlbrating_v1';
    let h = 2166136261 >>> 0;
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 16777619) >>> 0;
    }
    const r = 40 + (h % 61);
    return r;
}

async function getRoster(teamId: string): Promise<Player[]> {
    try {
        const res = await fetch(ROSTER_URL(teamId));
        if (!res.ok) throw new Error('roster fetch failed');
        const data = await res.json();
        const players: Player[] = ((data.roster as RosterItem[]) || []).map(item => {
            const pid = item.person?.id || Math.floor(Math.random() * 1e6);
            return {
                id: pid,
                name: item.person?.fullName || 'Unknown',
                position: item.position?.abbreviation || '',
                rating: idToRating(pid)
            };
        });
        return players;
    } catch (err) {
        console.error('讀取名單失敗:', err);
        return []; // Return an empty array on error
    }
}

export default getRoster;