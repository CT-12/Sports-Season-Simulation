import appStyle from "../styles/app.module.css";

interface TeamSelectProps {
  label: string;             // 標籤文字
  id: string;                // select 的 id
  teams: Team[];             // 隊伍陣列
}

function TeamSelect({ label, id, teams }: TeamSelectProps) {
    
    const teamOptions = teams.length > 0 ? teams.map(team => {
		return (
			<option key={team.id} value={team.id}>{team.name}</option>
		);
	}) : (
		<option value="">載入中…</option>
	);
    
    return (
        <div className={appStyle['select-wrap']}>
            <label>{label}</label>
            <select id={id}>
                {teamOptions}
            </select>
        </div>
    );
}

export default TeamSelect;