import { useState, useEffect } from 'react';
import appStyle from "./styles/app.module.css";
import TeamSelect from "./components/TeamSelect.tsx";
import Arena from "./components/Arena.tsx";
import SelectionMenu from "./components/SelectionMenu.tsx";
import { useTeamManager } from "./hooks/useTeamManager.ts";
import { computeWinProbability } from "./utils/ComputeTeamStat.ts";
import { analyzeMatchup } from "./api/Matchup.ts";
import UISlider from './components/UISlider.tsx';

function App() {
    const [mode, setMode] = useState('Team');
    const [teamStat, setTeamStat] = useState('pythagorean');
    
    // Team 模式的勝率（從後端獲取）
    const [teamModeWinProb, setTeamModeWinProb] = useState<{
        teamAWinProb: number;
        teamBWinProb: number;
    }>({ teamAWinProb: 50, teamBWinProb: 50 });
    
    const {
        teams,
        teamA,
        teamB,
        rosterA,
        rosterB,
        handleTeamSelect,
        movePlayer,
        resetRosters,
        hitterStat,
        pitcherStat,
        setHitterStat,
        setPitcherStat,
    } = useTeamManager();

    // Player 模式的勝率（基於球員 rating）
    const { teamAWinProb: playerModeTeamAProb, teamBWinProb: playerModeTeamBProb } = 
        computeWinProbability(rosterA, rosterB);
    
    // 當 Team 模式下，隊伍或方法改變時，呼叫後端 API 計算勝率
    useEffect(() => {
        const fetchTeamModeWinProb = async () => {
            // 只在 Team 模式且兩隊都已選擇時才呼叫
            if (mode !== 'Team' || teamA === '隊伍 A' || teamB === '隊伍 B') {
                setTeamModeWinProb({ teamAWinProb: 50, teamBWinProb: 50 });
                return;
            }
            
            console.log(`[App] Fetching matchup: ${teamA} vs ${teamB}, method: ${teamStat}`);
            
            // 呼叫後端 API
            const method = teamStat === 'pythagorean' ? 'Pythagorean' : 'Elo';
            const result = await analyzeMatchup(teamA, teamB, method);
            
            if (result && result.team_A_win_prob !== undefined && result.team_B_win_prob !== undefined) {
                setTeamModeWinProb({
                    teamAWinProb: result.team_A_win_prob,
                    teamBWinProb: result.team_B_win_prob
                });
                console.log(`[App] Win probabilities: A=${result.team_A_win_prob}%, B=${result.team_B_win_prob}%`);
            } else {
                console.error('[App] Failed to fetch win probabilities from backend');
                setTeamModeWinProb({ teamAWinProb: 50, teamBWinProb: 50 });
            }
        };
        
        fetchTeamModeWinProb();
    }, [mode, teamA, teamB, teamStat]);
    
    // 根據模式決定使用哪種勝率
    const finalTeamAWinProb = mode === 'Team' ? teamModeWinProb.teamAWinProb : playerModeTeamAProb;
    const finalTeamBWinProb = mode === 'Team' ? teamModeWinProb.teamBWinProb : playerModeTeamBProb;

    return (
        <div className={appStyle.app}>
            <header className={appStyle.header}>
                <div className={appStyle.headerLeft}></div>
                <div className={appStyle.titleGroup}>
                    <h1>⚾ MLB 對戰模擬器</h1>
                    <p className={appStyle.subtitle}>從後端API 讀取隊伍與名單</p>
                </div>
                <div className={appStyle.headerRight}>
                    <UISlider
                        options={['Team', 'Player']}
                        selected={mode}
                        onChange={setMode}
                    />
                </div>
            </header>

            <main>
                <SelectionMenu
                    mode={mode as 'Team' | 'Player'}
                    teamStat={teamStat}
                    setTeamStat={setTeamStat}
                    hitterStat={hitterStat}
                    setHitterStat={setHitterStat}
                    pitcherStat={pitcherStat}
                    setPitcherStat={setPitcherStat}
                />

                <TeamSelect
                    teams={teams}
                    onTeamsSelected={handleTeamSelect}
                    onResetRosters={resetRosters}
                    mode={mode}
                />

                <Arena
                    teamA={teamA}
                    teamB={teamB}
                    rosterA={rosterA}
                    rosterB={rosterB}
                    teamAWinProb={finalTeamAWinProb}
                    teamBWinProb={finalTeamBWinProb}
                    movePlayer={movePlayer}
                    mode={mode}
                    hitterStat={hitterStat}
                    pitcherStat={pitcherStat}
                    teams={teams}
                    teamStat={teamStat}
                />
            </main>
        </div>
    );
}

export default App;