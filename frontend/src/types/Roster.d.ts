interface Player {
    id: number,
    name: string,
    position: string,
    rating: number,
    displayValue?: number,  // 顯示用的原始值
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

interface PlayerCardProps {
    player: Player;
    belongTeam: string;
    mode: string;
    hitterStat: string;
    pitcherStat: string;
}