import appStyle from "../styles/app.module.css";
import PlayerCardStyle from "../styles/PlayerCard.module.css";
import ArenaStyle from "../styles/Arena.module.css";
import PlayerCard from "./PlayerCard";
import { getDisplayTeamName } from "../utils/DisplayTeamName";

function TeamPanel({ teamName, players, rating, winProb, onDragOver, onDrop, mode, hitterStat, pitcherStat, teams, teamStat }: TeamPanelProps) {
    const safePlayer = players ?? [];
    
    // 找到當前球隊的資料
    const currentTeam = teams?.find(t => t.name === teamName);
    
    // 取得顯示用的球隊名稱
    const displayName = getDisplayTeamName(teamName);
    
    // 根據 teamStat 決定顯示哪個分數
    const teamScore = teamStat === 'pythagorean' 
        ? currentTeam?.pythagoreanScore 
        : currentTeam?.eloScore;

    return (
        <div 
            className={ArenaStyle['team-panel']}
            onDragOver={onDragOver}
            onDrop={(e) => onDrop(e, teamName)}
        >
            <div className={ArenaStyle['panel-header']}>
                <div>
                    <h2>{displayName}</h2>
                    
                    {/* Team 模式：顯示球隊分數 */}
                    {mode === 'Team' && teamScore !== undefined && (
                        <div className={appStyle.sub}>
                            {teamStat === 'pythagorean' ? 'Pythagorean' : 'Elo'}: {teamScore.toFixed(2)}
                        </div>
                    )}
                    
                    {/* Player 模式：顯示球員數和 Rating */}
                    {mode === 'Player' && (
                        <div className={appStyle.sub}>
                            球員數：{safePlayer.length} · Rating：{rating}
                        </div>
                    )}
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
            
            {/* 顯示球員列表（Team 和 Player 模式都顯示） */}
            <div className={PlayerCardStyle["player-list"]}>
                {safePlayer.map(player => (
                    <PlayerCard 
                        key={player.id} 
                        player={player} 
                        belongTeam={teamName} 
                        mode={mode}
                        hitterStat={hitterStat}
                        pitcherStat={pitcherStat}
                    />
                ))}
            </div>
        </div>
    )
}

export default TeamPanel;