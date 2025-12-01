import { useState } from 'react';
import appStyle from "./styles/app.module.css";
import TeamSelect from "./components/TeamSelect.tsx";
import Arena from "./components/Arena.tsx";
import { useTeamManager } from "./hooks/useTeamManager.ts";
import { computeWinProbability } from "./utils/ComputeTeamStat.ts";
import UISlider from './components/UISlider.tsx';

function App() {
	const [mode, setMode] = useState('Team');
	const {
		teams,
		teamA,
		teamB,
		rosterA,
		rosterB,
		handleTeamSelect,
		movePlayer,
		resetRosters,
	} = useTeamManager();

	const { teamAWinProb, teamBWinProb } = computeWinProbability(rosterA, rosterB);

	return (
		<div className={appStyle.app}>
			<header className={appStyle.header}>
				<div className={appStyle.headerLeft}></div>
				<div className={appStyle.titleGroup}>
					<h1>⚾ MLB 對戰模擬器</h1>
					<p className={appStyle.subtitle}>
						從 MLB Stats API 讀取隊伍與名單，拖放球員交換陣容，依能力分數即時計算勝率
					</p>
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
				<TeamSelect
					teams={teams}
					onTeamsSelected={handleTeamSelect}
					onResetRosters={resetRosters}
				/>

				<Arena
					teamA={teamA}
					teamB={teamB}
					rosterA={rosterA}
					rosterB={rosterB}
					teamAWinProb={teamAWinProb}
					teamBWinProb={teamBWinProb}
					movePlayer={movePlayer}
					mode={mode}
				/>

				<section className={appStyle.notes}>
					<p>
						提示：若球員資料載入失敗（CORS），請啟動本地靜態伺服器或在後端做
						proxy。此版本用 deterministic 隨機法為每位球員產生
						rating（可改為使用真實數據）。
					</p>
				</section>
			</main>

			<footer>
				<small>資料來源：MLB Stats API（https://statsapi.mlb.com）</small>
			</footer>
		</div>
	);
}

export default App;
