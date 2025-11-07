import { useEffect, useState } from "react";
// Style
import appStyle from "../styles/app.module.css";
import PlayerCardStyle from "../styles/PlayerCard.module.css";
import ArenaStyle from "../styles/Arena.module.css";
// Component
import PlayerCard from "./PlayerCard";
// Utils
// import { handleDragOver, handleDrop } from "../utils/handlers";

function TeamPanel({ teamName, players, rating, winProb, onDragOver, onDrop }: TeamPanelProps) {

    return (
        <div 
            className={ArenaStyle['team-panel']}
            onDragOver={onDragOver}
            onDrop={(e) => onDrop(e, teamName)}
        >
            <div className={ArenaStyle['panel-header']}>
                <div>
                    <h2>{ teamName }</h2>
                    <div className={appStyle.sub}>
                        球員數：{players.length} · Rating：{rating}
                    </div>
                </div>
                <div className={appStyle['win-block']}>
                    <div className={appStyle['win-label']}>勝率</div>
                    <div className={appStyle['bar']}>
                        <div className={appStyle['fill']} style={{ width: `${winProb}%` }}></div>
                    </div>
                    <div className={appStyle['win-percent']}>
                        {winProb}%
                    </div>
                </div>
            </div>
            <div className={PlayerCardStyle["player-list"]}>
                {players.map(player => (
                    <PlayerCard key={player.id} player={player} belongTeam={teamName}/>
                ))}
            </div>
        </div>
    )
}

export default TeamPanel