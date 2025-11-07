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
}