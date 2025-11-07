import { useState, useEffect } from "react"
// Utils
import getTeams from "../api/GetTeams.ts"
import getRoster from "../api/GetRoster.ts";

export function useTeamManager() {
    const [teams, setTeams] = useState<Team[]>([])

	useEffect(() => {
		getTeams().then((fetchedTeams) => {
			setTeams(fetchedTeams)
		})
	}, [])

	const [teamA, setTeamA] = useState("隊伍 A");
	const [teamB, setTeamB] = useState("隊伍 B");
	const [rosterA, setRosterA] = useState<Player[]>([]);
	const [rosterB, setRosterB] = useState<Player[]>([]);
    const [originalRosterA, setOriginalRosterA] = useState<Player[]>([]);
    const [originalRosterB, setOriginalRosterB] = useState<Player[]>([]);

	const handleTeamSelect = async (
		side: "A" | "B", 
		teamId: number, 
		teamName: string
	) => {
		if (!teamName) {
			if (side === "A") {
                setRosterA([]);
                setOriginalRosterA([]);
            } else {
                setRosterB([]);
                setOriginalRosterB([]);
            }
			return;
		}
		const roster = await getRoster(teamId);
		if (side === "A") {
			setTeamA(teamName);
			setRosterA(roster);
            setOriginalRosterA(roster);
		} else {
			setTeamB(teamName);
			setRosterB(roster);
            setOriginalRosterB(roster);
		}
	};

	const movePlayer = (
        player: Player,      // 被移動的球員資料
        sourceTeam: string, // 來源隊伍名稱 (例如 '隊伍 A')
        targetTeam: string  // 目標隊伍名稱 (例如 '隊伍 B')
    ) => {
        if (sourceTeam === targetTeam) {
            return;
        }
    
        // From A to B
        if (sourceTeam === teamA && targetTeam === teamB) {
            setRosterA(prev => prev.filter(p => String(p.id) !== String(player.id)));
            setRosterB(prev => [...prev, player]);
        } 
        // From B to A
        else if (sourceTeam === teamB && targetTeam === teamA) {
            setRosterB(prev => prev.filter(p => String(p.id) !== String(player.id)));
            setRosterA(prev => [...prev, player]);
        }
    };

    const resetRosters = () => {
        setRosterA(originalRosterA);
        setRosterB(originalRosterB);
    };

    return {
        teams,
        teamA,
        teamB,
        rosterA,
        rosterB,
        handleTeamSelect,
		movePlayer,
        resetRosters
    };
}
