interface ArenaProps {
    teamA: string;
    teamB: string;
    rosterA: Player[];
    rosterB: Player[];
    teamAWinProb: number;
    teamBWinProb: number;
    movePlayer: (
        player: Player,
        sourceTeam: string,
        targetTeam: string
    ) => void;
    mode: string;
    hitterStat: string;
    pitcherStat: string;
    teams?: Team[];
    teamStat?: string;
}