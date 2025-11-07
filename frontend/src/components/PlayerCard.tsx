//Style
import playCardStyle from "../styles/PlayerCard.module.css";

function PlayerCard({ player, belongTeam }: PlayCardProps) {
    
    // Drag handler: 加在「被拖曳的物品」上的監聽器。
    const handleDragStart = (e: React.DragEvent<HTMLDivElement>) => {
        e.currentTarget.classList.add("dragging");
        e.dataTransfer.setData('text/plain', JSON.stringify({
            id: e.currentTarget.dataset.playerId,
            name: e.currentTarget.dataset.name,
            position: e.currentTarget.dataset.pos,
            rating: e.currentTarget.dataset.rating,
            teamName: belongTeam
        }));
        e.dataTransfer.effectAllowed = 'move';
    }
    const handleDragEnd = (e: React.DragEvent<HTMLDivElement>) => {
        e.currentTarget.classList.remove("dragging");
    }

    return (
        <div
            className={playCardStyle['player-card']}
            draggable={true}
            data-player-id={player.id}
            data-name={player.name}
            data-pos={player.position}
            data-rating={player.rating}
            onDragStart={handleDragStart}
            onDragEnd={handleDragEnd}
        >
            <div className="name">{player.name}</div>
            <div className="pos">{player.position || ''}</div>
            <div className="rating">
                <div className="score">{player.rating}</div>
                <div className="bar">
                    <div
                        className="fill"
                        style={{ width: `${((player.rating - 40) / 60) * 100}%` }}
                    ></div>
                </div>
            </div>
        </div>
    );
}

export default PlayerCard;
