import type { TeamSeasonResult } from '../api/SeasonSimulation';
import styles from '../styles/SimulationResults.module.css';

interface SimulationResultsProps {
  nlTeams: TeamSeasonResult[];
  alTeams: TeamSeasonResult[];
  onClose: () => void;
}

function SimulationResults({ nlTeams, alTeams, onClose }: SimulationResultsProps) {
  const renderLeague = (title: string, teams: TeamSeasonResult[]) => (
    <div className={styles.league}>
      <h2 className={styles.leagueTitle}>{title}</h2>
      <div className={styles.tableContainer}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th className={styles.rankCol}>排名</th>
              <th className={styles.logoCol}></th>
              <th className={styles.teamCol}>球隊</th>
            </tr>
          </thead>
          <tbody>
            {teams.map((team) => (
              <tr key={team.team} className={styles.row}>
                <td className={styles.rankCol}>
                  <span className={styles.rankBadge}>{team.rank}</span>
                </td>
                <td className={styles.logoCol}>
                  {team.logo && (
                    <img 
                      src={team.logo} 
                      alt={team.team}
                      className={styles.logo}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  )}
                </td>
                <td className={styles.teamCol}>{team.team}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h1 className={styles.title}>🏆 2026 賽季預測結果</h1>
          <button className={styles.closeButton} onClick={onClose}>✕</button>
        </div>
        
        <div className={styles.content}>
          <div className={styles.leagues}>
            {renderLeague('National League', nlTeams)}
            {renderLeague('American League', alTeams)}
          </div>
        </div>
        
        <div className={styles.footer}>
          <p className={styles.note}>
            * 此排名基於蒙地卡羅模擬 2026 賽季結果
          </p>
        </div>
      </div>
    </div>
  );
}

export default SimulationResults;
