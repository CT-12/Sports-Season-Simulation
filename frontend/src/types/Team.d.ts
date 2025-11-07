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
    teams: { id: number; name: string }[];
    onTeamsSelected: (side: "A" | "B", teamId: number, teamName: string) => void;
    onResetRosters: () => void;
}