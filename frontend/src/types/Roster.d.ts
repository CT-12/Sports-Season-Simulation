interface Player {
    id: number,
    name: string,
    position: string,
    rating: number,
}

interface RosterItem {
    person: {
        id: number;
        fullName: string;
    };
    position: {
        abbreviation: string;
    };
}

interface PlayCardProps {
    player: Player;
    belongTeam: string;
    mode: string;
}