interface Team {
    id: number,
    name: string,
}

interface TeamPanelProps {
    teamName: string;
    players: Player[];
}

interface TeamSelectProps {
    label: string;
    id: string;
    teams: Team[];
    onTeamSelect: (teamId: string) => void;
}