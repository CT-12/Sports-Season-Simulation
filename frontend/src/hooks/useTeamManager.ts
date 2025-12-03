import { useState, useEffect } from "react"
import getTeams from "../api/GetTeams.ts"
import getRoster from "../api/GetRoster.ts"

export function useTeamManager() {
    const [teams, setTeams] = useState<Team[]>([])
    const [teamA, setTeamA] = useState("隊伍 A")
    const [teamB, setTeamB] = useState("隊伍 B")
    const [rosterA, setRosterA] = useState<Player[]>([])
    const [rosterB, setRosterB] = useState<Player[]>([])
    const [originalRosterA, setOriginalRosterA] = useState<Player[]>([])
    const [originalRosterB, setOriginalRosterB] = useState<Player[]>([])
    const [teamAId, setTeamAId] = useState<number | null>(null)
    const [teamBId, setTeamBId] = useState<number | null>(null)
    
    // 指標 state（與 SelectionMenu 的 value 對應）
    const [hitterStat, setHitterStat] = useState('ops') // OPS
    const [pitcherStat, setPitcherStat] = useState('era')  // ERA

    useEffect(() => {
        getTeams().then((fetchedTeams) => {
            setTeams(fetchedTeams)
        })
    }, [])

    const handleTeamSelect = async (
        side: "A" | "B", 
        teamId: number, 
        teamName: string
    ) => {
        if (!teamName) {
            if (side === "A") {
                setRosterA([])
                setOriginalRosterA([])
                setTeamAId(null)
                setTeamA("隊伍 A")
            } else {
                setRosterB([])
                setOriginalRosterB([])
                setTeamBId(null)
                setTeamB("隊伍 B")
            }
            return
        }
        
        const roster = await getRoster(teamId, teamName, hitterStat, pitcherStat)
        
        if (side === "A") {
            setTeamA(teamName)
            setRosterA(roster)
            setOriginalRosterA(roster)
            setTeamAId(teamId)
        } else {
            setTeamB(teamName)
            setRosterB(roster)
            setOriginalRosterB(roster)
            setTeamBId(teamId)
        }
    }

    // 當指標改變時，重新撈兩隊名單
    const handleHitterStatChange = async (newStat: string) => {
        setHitterStat(newStat)
        // 重新撈 A 隊
        if (teamAId && teamA !== "隊伍 A") {
            const roster = await getRoster(teamAId, teamA, newStat, pitcherStat)
            setRosterA(roster)
            setOriginalRosterA(roster)
        }
        // 重新撈 B 隊
        if (teamBId && teamB !== "隊伍 B") {
            const roster = await getRoster(teamBId, teamB, newStat, pitcherStat)
            setRosterB(roster)
            setOriginalRosterB(roster)
        }
    }

    const handlePitcherStatChange = async (newStat: string) => {
        setPitcherStat(newStat)
        // 重新撈 A 隊
        if (teamAId && teamA !== "隊伍 A") {
            const roster = await getRoster(teamAId, teamA, hitterStat, newStat)
            setRosterA(roster)
            setOriginalRosterA(roster)
        }
        // 重新撈 B 隊
        if (teamBId && teamB !== "隊伍 B") {
            const roster = await getRoster(teamBId, teamB, hitterStat, newStat)
            setRosterB(roster)
            setOriginalRosterB(roster)
        }
    }

    const movePlayer = (
        player: Player,
        sourceTeam: string,
        targetTeam: string
    ) => {
        if (sourceTeam === targetTeam) return
    
        if (sourceTeam === teamA && targetTeam === teamB) {
            setRosterA(prev => prev.filter(p => String(p.id) !== String(player.id)))
            setRosterB(prev => [...prev, player])
        } 
        else if (sourceTeam === teamB && targetTeam === teamA) {
            setRosterB(prev => prev.filter(p => String(p.id) !== String(player.id)))
            setRosterA(prev => [...prev, player])
        }
    }

    const resetRosters = () => {
        setRosterA(originalRosterA)
        setRosterB(originalRosterB)
    }

    return {
        teams,
        teamA,
        teamB,
        rosterA,
        rosterB,
        handleTeamSelect,
        movePlayer,
        resetRosters,
        hitterStat,
        pitcherStat,
        setHitterStat: handleHitterStatChange,
        setPitcherStat: handlePitcherStatChange,
    }
}