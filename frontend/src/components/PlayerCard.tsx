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

    const pos = player.position ?? "";
    const pitcher = isPitcher(pos);

    // 將 value key 轉成顯示標籤
    const metricLabel = (key: string) => {
        const map: Record<string, string> = {
            'ops': 'OPS',
            'h_war': 'WAR',
            'avg': 'AVG',
            'era': 'ERA',
            'p_war': 'WAR',
            'whip': 'WHIP',
        };
        return map[key] || key.toUpperCase();
    };

    const currentMetric = pitcher ? metricLabel(pitcherStat ?? 'era') : metricLabel(hitterStat ?? 'ops');
    
    // 顯示值：優先使用 displayValue，如果沒有則用 rating
    const displayedValue = player.displayValue !== undefined ? player.displayValue : player.rating;
    
    // 格式化顯示值（如果是 AVG、OPS、ERA、WHIP 這種小數，保留 3 位小數）
    const formatValue = (val: number, metric: string) => {
        if (val === 0 || val === null || val === undefined) {
            return '-';
        }
        const lowerMetric = metric.toLowerCase();
        if (lowerMetric === 'avg' || lowerMetric === 'ops' || lowerMetric === 'era' || lowerMetric === 'whip') {
            return val.toFixed(3);
        }
        return val.toFixed(1);
    };

    return (
        <div
            className={PlayerCardStyle["player-card"]}
            draggable={mode === 'Player'}
            onDragStart={handleDragStart}
        >
            <div className={PlayerCardStyle["player-name"]}>{player.name}</div>
            <div className={PlayerCardStyle["player-position"]}>位置：{pos || "N/A"}</div>
            <div className={PlayerCardStyle["player-rating"]}>
                分數：<strong>{formatValue(displayedValue, currentMetric)}</strong>
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