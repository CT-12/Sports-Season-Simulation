import { useState, useEffect } from "react";
import appStyle from "./styles/app.module.css";
import getTeams from "./api/getTeams.ts";
// Components
import TeamSelect from "./components/TeamSelect";

function App() {
	const [teams, setTeams] = useState<Team[]>([]);

	useEffect(() => {
		getTeams().then((fetchedTeams) => {
			setTeams(fetchedTeams);
		});
	}, []);

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
					/>
					<div className={appStyle.vs}>VS</div>
					<TeamSelect
						label="隊伍 B"
						id="teamBSelect"
						teams={teams}
					/>
					<button id="resetBtn" title="還原原始名單">
						重置陣容
					</button>
				</section>

				<section className={appStyle.arena}>
					<div className={appStyle.teamPanel} id="teamA">
						<div className={appStyle.panelHeader}>
							<div>
								<h2 id="teamAName">隊伍 A</h2>
								<div className={appStyle.sub} id="teamAInfo">
									球員數：0 · Rating：0
								</div>
							</div>
							<div className={appStyle.winBlock}>
								<div className={appStyle.winLabel}>勝率</div>
								<div className={appStyle.bar} id="winBarA">
									<div className={appStyle.fill} style={{ width: "0%" }}></div>
								</div>
								<div className={appStyle.winPercent} id="winPctA">
									--
								</div>
							</div>
						</div>
						<div
							className={appStyle.playerList}
							id="rosterA"
							data-side="A"
						></div>
					</div>

					<div className={appStyle.teamPanel} id="teamB">
						<div className={appStyle.panelHeader}>
							<div>
								<h2 id="teamBName">隊伍 B</h2>
								<div className={appStyle.sub} id="teamBInfo">
									球員數：0 · Rating：0
								</div>
							</div>
							<div className={appStyle.winBlock}>
								<div className={appStyle.winLabel}>勝率</div>
								<div className={appStyle.bar} id="winBarB">
									<div className={appStyle.fill} style={{ width: "0%" }}></div>
								</div>
								<div className={appStyle.winPercent} id="winPctB">
									--
								</div>
							</div>
						</div>
						<div
							className={appStyle.playerList}
							id="rosterB"
							data-side="B"
						></div>
					</div>
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
