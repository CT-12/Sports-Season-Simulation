import { useState } from 'react';
// Style
import TeamSelectStyle from "../styles/TeamSelect.module.css";
// Hooks
import { useTeamSelect } from "../hooks/useTeamSelect.ts";
// Components
import SelectionMenu from './SelectionMenu.tsx';

function TeamSelect({ teams, onTeamsSelected, onResetRosters, mode }: TeamSelectProps) {

    const {
        selectedTeams,
        modalOpen,
        handleTeamSelectClick,
        openModal,
        closeModal,
        confirmSelection
    } = useTeamSelect({ onTeamsSelected, teams });

    const [teamStat, setTeamStat] = useState('pythagorean');
    const [hitterStat, setHitterStat] = useState('ops_plus');
    const [pitcherStat, setPitcherStat] = useState('p_war');


    return (
        <>
        <SelectionMenu
            mode={mode as 'Team' | 'Player'}
            teamStat={teamStat}
            setTeamStat={setTeamStat}
            hitterStat={hitterStat}
            setHitterStat={setHitterStat}
            pitcherStat={pitcherStat}
            setPitcherStat={setPitcherStat}
        />

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
                onClick={()=>{}} // TODO: implement simulate function
            >
                開始模擬
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
                            <img src={`https://www.mlbstatic.com/team-logos/team-cap-on-light/${team.id}.svg`} alt={team.name} />
                            <span>{team.name}</span>
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