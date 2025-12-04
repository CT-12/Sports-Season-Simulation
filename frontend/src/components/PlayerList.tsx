import playerListStyle from "../styles/playerList.module.css";

interface Player {
    id: number;
    name: string;
    position: string;
    rating: number;
    metricUsed?: string;
}

interface PlayerListProps {
    players: Player[];
    teamName: string;
    onPlayerClick: (player: Player) => void;
    hitterMetric?: string;
    pitcherMetric?: string;
}

export default function PlayerList({
    players,
    teamName,
    onPlayerClick,
    hitterMetric = 'OPS+',
    pitcherMetric = 'ERA'
}: PlayerListProps) {
    const isPitcher = (position: string) => 
        position.toLowerCase().includes('pitcher') || position === 'P';
    
    return (
        <div className={playerListStyle.playerList}>
            {players.length === 0 ? (
                <p className={playerListStyle.emptyMessage}>尚未選擇球員</p>
            ) : (
                players.map((player) => (
                    <div 
                        key={player.id}
                        className={playerListStyle.playerCard}
                        onClick={() => onPlayerClick(player)}
                    >
                        <div className={playerListStyle.playerCardContent}>
                            <h4 className={playerListStyle.playerName}>{player.name}</h4>
                            <p className={playerListStyle.playerPosition}>位置：{player.position}</p>
                            <div className={playerListStyle.ratingSection}>
                                <p className={playerListStyle.ratingBadge}>
                                    分數：<strong>{player.rating}</strong>
                                </p>
                                <p className={playerListStyle.metricLabel}>
                                    ({isPitcher(player.position) ? pitcherMetric : hitterMetric})
                                </p>
                            </div>
                        </div>
                    </div>
                ))
            )}
        </div>
    );
}
