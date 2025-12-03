import PlayerCardStyle from "../styles/PlayerCard.module.css";

function PlayerCard({ player, belongTeam, mode, hitterStat, pitcherStat }: PlayerCardProps) {
    const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
        if (mode !== 'Player') return;
        const payload = {
            id: player.id,
            name: player.name,
            rating: player.rating,
            position: player.position,
            teamName: belongTeam
        };
        e.dataTransfer.setData('text/plain', JSON.stringify(payload));
        e.dataTransfer.effectAllowed = 'move';
    }

    const isPitcher = (pos?: string) => !!pos && (pos.toLowerCase().includes("pitcher") || pos === "P");
    const isTwoWay = (pos?: string) => !!pos && pos.toLowerCase().includes("two");

    const pos = player.position ?? "";
    const twoWay = isTwoWay(pos);
    const pitcher = isPitcher(pos);

    // 將 value key 轉成顯示標籤（ops_plus → OPS+）
    const metricLabel = (key: string) => {
        const map: Record<string, string> = {
            'ops_plus': 'OPS+',
            'h_war': 'WAR',
            'wrc_plus': 'wRC+',
            'p_war': 'WAR',
            'era': 'ERA',
            'whip': 'WHIP',
        };
        return map[key] || key.toUpperCase();
    };

    const currentMetric = pitcher ? metricLabel(pitcherStat ?? 'p_war') : metricLabel(hitterStat ?? 'ops_plus');

    return (
        <div
            className={PlayerCardStyle["player-card"]}
            draggable={mode === 'Player'}
            onDragStart={handleDragStart}
        >
            <div className={PlayerCardStyle["player-name"]}>{player.name}</div>
            <div className={PlayerCardStyle["player-position"]}>位置：{pos || "N/A"}</div>
            <div className={PlayerCardStyle["player-rating"]}>
                分數：<strong>{player.rating ?? '-'}</strong>
                <span style={{ 
                    marginLeft: '6px', 
                    fontSize: '0.85em', 
                    fontStyle: 'italic', 
                    color: '#999',
                    fontWeight: 'normal'
                }}>
                    ({currentMetric})
                </span>
            </div>
        </div>
    );
}

export default PlayerCard;