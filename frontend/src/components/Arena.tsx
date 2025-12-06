// Style
import ArenaStyle from "../styles/Arena.module.css";
// Components
import TeamPanel from "./TeamPanel";
// Utils
import { computeTeamRating } from "../utils/ComputeTeamStat";
import { getUniqueTransactions } from "../utils/TransactionUtils"

function Arena({ teamA, teamB, rosterA, rosterB, teamAWinProb, teamBWinProb, movePlayer, mode, hitterStat, pitcherStat, teams, teamStat, setTransactions }: ArenaProps) {
    // 加在「放置的目標區」上的監聽器。
    // 移動到「目標區域」的上方時
    const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => { 
        if (mode !== 'Player') return;
        e.preventDefault(); // 必須要有這行，才能允許放置（drop）
        e.dataTransfer.dropEffect = 'move';
    }
    // 在「目標區域」上方放開滑鼠按鍵時
    const handleDrop = (e: React.DragEvent<HTMLDivElement>, teamName: string) => { 
        if (mode !== 'Player') return;
        e.preventDefault();
        const payload = e.dataTransfer.getData('text/plain');
        if (!payload) return;
        const data = JSON.parse(payload);

        const sourceTeam: string = data.teamName;
        const targetTeam: string = teamName;
        // if dragging from same container and dropped inside, ignore
        if (sourceTeam && sourceTeam === targetTeam) {
            // do nothing (or re-order if needed)
            return;
        }
        
        let p: Player = {
            id: data.id,
            name: data.name,
            rating: Number(data.rating),
            position: data.position
        }
        // remove from old parent and append to new
        movePlayer(p, sourceTeam, targetTeam);

        // Log transaction
        const transaction = {
            player_name: p.name,
            position: p.position,
            from_team: sourceTeam,
            to_team: targetTeam
        }
        setTransactions((prev: Transaction[]) => {
            const allTransactions = [...prev, transaction];
            return getUniqueTransactions(allTransactions);
        });
    }

    return (
        <div className={ArenaStyle.arena}>
            <TeamPanel 
                teamName={teamA} 
                players={rosterA} 
                rating={computeTeamRating(rosterA)} 
                winProb={teamAWinProb} 
                onDragOver={handleDragOver} 
                onDrop={handleDrop}
                mode={mode}
                hitterStat={hitterStat}
                pitcherStat={pitcherStat}
                teams={teams}
                teamStat={teamStat}
            />
            <TeamPanel 
                teamName={teamB} 
                players={rosterB} 
                rating={computeTeamRating(rosterB)} 
                winProb={teamBWinProb} 
                onDragOver={handleDragOver} 
                onDrop={handleDrop}
                mode={mode}
                hitterStat={hitterStat}
                pitcherStat={pitcherStat}
                teams={teams}
                teamStat={teamStat}
            />
        </div>
    )
}

export default Arena;