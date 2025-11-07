interface Team {
    id: number;
    name: string;
}

interface TeamPanelProps {
    teamName: string;
    players: Player[];
    rating: number;
    winProb: number;
    onDragOver: (e: React.DragEvent<HTMLDivElement>) => void;
    onDrop: (e: React.DragEvent<HTMLDivElement>, teamName: string) => void;
}

interface TeamSelectProps {
    label: string;
    id: string;
    teams: Team[];
    onTeamSelect: (teamId: number, teamName: string) => void;
}