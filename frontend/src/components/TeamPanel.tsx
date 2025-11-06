// Style
import appStyle from "../styles/app.module.css";
import PlayerCardStyle from "../styles/PlayerCard.module.css";
import ArenaStyle from "../styles/Arena.module.css";
// Component
import PlayerCard from "./PlayerCard";


function TeamPanel({ teamName, players }: TeamPanelProps) {

    return (
        <div className={ArenaStyle['team-panel']}>
            <div className={ArenaStyle['panel-header']}>
                <div>
                    <h2>{ teamName }</h2>
                    <div className={appStyle.sub}>
                        球員數：{players.length} · Rating：0
                    </div>
                </div>
                <div className={appStyle['win-block']}>
                    <div className={appStyle['win-label']}>勝率</div>
                    <div className={appStyle['bar']}>
                        <div className={appStyle['fill']} style={{ width: "0%" }}></div>
                    </div>
                    <div className={appStyle['win-percent']}>
                        --
                    </div>
                </div>
            </div>
            <div className={PlayerCardStyle["player-list"]}>
                {players.map(player => (
                    <PlayerCard key={player.id} player={player} />
                ))}
            </div>
        </div>
    )
}

export default TeamPanel