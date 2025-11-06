import appStyle from "../styles/app.module.css";

function TeamSelect({ label, id, teams, onTeamSelect }: TeamSelectProps) {
    
    const teamOptions = teams.length > 0 ? teams.map(team => {
		return (
			<option key={team.id} value={team.id}>{team.name}</option>
		);
	}) : (
		<option value="">載入中…</option>
	);

    const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        onTeamSelect(event.target.value);
    };
    
    return (
        <div className={appStyle['select-wrap']}>
            <label>{label}</label>
            <select id={id} onChange={handleChange}>
                <option value="">-- 請選擇 --</option>
                {teamOptions}
            </select>
        </div>
    );
}

export default TeamSelect;