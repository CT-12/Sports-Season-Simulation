import { useState, useEffect } from "react"
// Style
import appStyle from "./styles/app.module.css"
import ArenaStyle from "./styles/Arena.module.css"
// Components
import TeamSelect from "./components/TeamSelect"
import TeamPanel from "./components/TeamPanel.tsx"
// Utils
import getTeams from "./api/getTeams.ts"
import getRoster from "./api/GetRoster.ts";

function App() {
	const [teams, setTeams] = useState<Team[]>([])

	useEffect(() => {
		getTeams().then((fetchedTeams) => {
			setTeams(fetchedTeams)
		})
	}, [])

	const [rosterA, setRosterA] = useState<Player[]>([]);
	const [rosterB, setRosterB] = useState<Player[]>([]);

	const handleTeamChange = async (side: "A" | "B", teamId: string) => {
		if (!teamId) {
			side === "A" ? setRosterA([]) : setRosterB([]);
			return;
		}
		const roster = await getRoster(teamId);
		if (side === "A") {
			setRosterA(roster);
		} else {
			setRosterB(roster);
		}
	};

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
				<section className={appStyle.controls}>
					<TeamSelect
						label="隊伍 A"
						id="teamASelect"
						teams={teams}
						onTeamSelect={(teamId) => handleTeamChange("A", teamId)}
					/>
					<div className={appStyle.vs}>VS</div>
					<TeamSelect
						label="隊伍 B"
						id="teamBSelect"
						teams={teams}
						onTeamSelect={(teamId) => handleTeamChange("B", teamId)}
					/>
					<button id="resetBtn" title="還原原始名單">
						重置陣容
					</button>
				</section>

				<section className={ArenaStyle.arena}>
					<TeamPanel teamName="隊伍 A" players={rosterA} />
					<TeamPanel teamName="隊伍 B" players={rosterB} />
				</section>

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
