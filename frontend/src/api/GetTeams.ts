const TEAM_LIST_URL: string = 'https://statsapi.mlb.com/api/v1/teams?sportId=1'

async function getTeams(): Promise<Team[]> {
    try{
        const res = await fetch(TEAM_LIST_URL)
        if (!res.ok) throw new Error('Failed to fetch team list')
        const data = await res.json()
        const teams: Team[] = data.teams

        return teams
    } catch (error) {
        console.error(error)
        const mockTeams = [
            {id:109, name:'Los Angeles Dodgers'},
            {id:147, name:'New York Yankees'},
            {id:117, name:'Houston Astros'},
            {id:144, name:'Atlanta Braves'}
        ];

        return mockTeams
    }
}

export default getTeams