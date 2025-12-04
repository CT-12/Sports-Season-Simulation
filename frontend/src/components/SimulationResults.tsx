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
              <th className={styles.winsCol}>勝</th>
              <th className={styles.lossesCol}>負</th>
              <th className={styles.pctCol}>勝率</th>
            </tr>
          </thead>
          <tbody>
            {teams.map((team) => {
              const winPct = (team.wins / (team.wins + team.losses)).toFixed(3);
              return (
                <tr key={team.team} className={styles.row}>
                  <td className={styles.rankCol}>{team.rank}</td>
                  <td className={styles.logoCol}>
                    {team.logo && (
                      <img 
                        src={team.logo} 
                        alt={team.team}
                        className={styles.logo}
                        onError={(e) => {
                          // 如果圖片加載失敗，隱藏它
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    )}
                  </td>
                  <td className={styles.teamCol}>{team.team}</td>
                  <td className={styles.winsCol}>{team.wins}</td>
                  <td className={styles.lossesCol}>{team.losses}</td>
                  <td className={styles.pctCol}>{winPct}</td>
                </tr>
              );
            })}
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
            * 此結果基於蒙地卡羅模擬，模擬 162 場比賽的結果
          </p>
        </div>
      </div>
    </div>
  );
}

export default SimulationResults;
