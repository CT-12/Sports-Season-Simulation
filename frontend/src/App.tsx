// Style
import appStyle from "./styles/app.module.css";
// Components
import TeamSelect from "./components/TeamSelect.tsx";
import Arena from "./components/Arena.tsx";
// Hooks
import {useTeamManager} from "./hooks/useTeamManager.ts";

import {computeWinProbability} from "./utils/ComputeTeamStat.ts";

function App() {

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
		<>
			<header>
				<h1>⚾ MLB 對戰模擬器</h1>
				<p className="subtitle">
					從 MLB Stats API
					讀取隊伍與名單，拖放球員交換陣容，依能力分數即時計算勝率
				</p>
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
		</>
	);
}

export default App;
