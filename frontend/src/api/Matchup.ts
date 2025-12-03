const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export async function analyzeMatchup(
  teamAName: string,
  teamBName: string,
  method: 'Pythagorean' | 'Elo' = 'Pythagorean'
): Promise<any | null> {
  const url = `${API_BASE}/matchup/`;
  const payload = {
    team_A: teamAName,
    team_B: teamBName,
    method,
  };

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    const ct = res.headers.get('content-type') || '';
    if (!res.ok) {
      console.error('[Matchup] backend error', res.status, text?.slice(0, 500));
      return null;
    }
    if (!ct.includes('application/json')) {
      console.error('[Matchup] unexpected content-type', ct);
      return null;
    }
    return text ? JSON.parse(text) : null;
  } catch (e) {
    console.error('[Matchup] fetch failed', e);
    return null;
  }
}

export default analyzeMatchup;