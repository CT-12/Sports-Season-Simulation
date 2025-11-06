import playCardStyle from "../styles/PlayerCard.module.css";

function PlayerCard({ player }: PlayCardProps) {
    return (
        <div
            className={playCardStyle['player-card']}
            draggable={true}
            data-player-id={player.id}
            data-name={player.name}
            data-pos={player.position}
            data-rating={player.rating}
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
