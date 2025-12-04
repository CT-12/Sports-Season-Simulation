import TeamSelectStyle from "../styles/TeamSelect.module.css";
import { useTeamSelect } from "../hooks/useTeamSelect.ts";
import { getDisplayTeamName } from "../utils/DisplayTeamName";

function TeamSelect({ teams, onTeamsSelected, onResetRosters, onRunSimulation, isSimulating }: TeamSelectProps) {

    const {
        selectedTeams,
        modalOpen,
        handleTeamSelectClick,
        openModal,
        closeModal,
        confirmSelection
    } = useTeamSelect({ onTeamsSelected, teams });

    // 取得球隊 Logo URL
    const getTeamLogo = (team: Team) => {
        // 優先使用 API 提供的 logoUrl，否則使用預設格式
        const url = team.logoUrl || `https://www.mlbstatic.com/team-logos/${team.id}.svg`;
        console.log(`[TeamSelect] Logo URL for ${team.name} (id: ${team.id}):`, url);
        return url;
    };

    return (
        <>
        <div id="btnContainer" className={TeamSelectStyle["button-container"]}>
            <button 
                id="openModalBtn" 
                className={TeamSelectStyle["trigger-btn"]}
                onClick={openModal}
            >
                選擇隊伍
            </button>

            <button 
                id="resetBtn" 
                className={TeamSelectStyle["trigger-btn"]}
                onClick={onResetRosters}
            >
                重置陣容
            </button>

            <button 
                id="simulateBtn" 
                className={TeamSelectStyle["trigger-btn"]}
                onClick={onRunSimulation}
                disabled={isSimulating}
            >
                {isSimulating ? '⏳ 正在執行蒙地卡羅模擬...' : '開始模擬'}
            </button>
        </div>

        <div id="teamModal" className={`${TeamSelectStyle.modal} ${modalOpen ? TeamSelectStyle['modal-active'] : ''}`}>
            <div className={TeamSelectStyle["modal-content"]}>
                <span id="closeModalBtn" className={TeamSelectStyle["close-btn"]} onClick={closeModal}>&times;</span>
                <h2>請選擇兩個隊伍</h2>
                <p id="selectionHint">已選擇: {selectedTeams.length} / 2</p>

                <div id="teamListContainer" className={TeamSelectStyle["team-list"]}>
                    {teams.map((team) => (
                        <div 
                            key={team.id} 
                            className={`${TeamSelectStyle["team-item"]} ${selectedTeams.includes(team.id) ? TeamSelectStyle['selected'] : ''}`} 
                            data-team-id={team.id}
                            onClick={() => handleTeamSelectClick(team.id)}
                        >
                            <img 
                                src={getTeamLogo(team)} 
                                alt={team.name}
                                onLoad={() => console.log(`[TeamSelect] ✓ Logo loaded: ${team.name}`)}
                                onError={(e) => {
                                    const target = e.currentTarget;
                                    console.error(`[TeamSelect] ✗ Logo failed for ${team.name}, trying fallback...`);
                                    
                                    // 嘗試備用的圖片來源
                                    if (target.src.includes('/team-logos/') && !target.src.includes('/team-cap-on-light/')) {
                                        console.log(`[TeamSelect] Trying cap-on-light version...`);
                                        target.src = `https://www.mlbstatic.com/team-logos/team-cap-on-light/${team.id}.svg`;
                                    } else if (target.src.includes('/team-cap-on-light/')) {
                                        console.log(`[TeamSelect] Trying ESPN version...`);
                                        target.src = `https://a.espncdn.com/combiner/i?img=/i/teamlogos/mlb/500/${team.id}.png`;
                                    } else if (target.src.includes('espncdn.com')) {
                                        console.log(`[TeamSelect] Trying midfield logo...`);
                                        target.src = `https://midfield.mlbstatic.com/v1/team/${team.id}/spots/256`;
                                    } else {
                                        console.error(`[TeamSelect] All sources failed for ${team.name}`);
                                        target.style.display = 'none';
                                    }
                                }}
                            />
                            <span>{getDisplayTeamName(team.name)}</span>
                        </div>
                    ))}
                </div>

                <div className={TeamSelectStyle["modal-footer"]}>
                    <button 
                        id="confirmSelectionBtn" 
                        className={TeamSelectStyle["confirm-btn"]} disabled={selectedTeams.length !== 2}
                        onClick={confirmSelection}
                    >
                        確定
                    </button>
                </div>
            </div>
        </div>
        </>
    )
}

export default TeamSelect;