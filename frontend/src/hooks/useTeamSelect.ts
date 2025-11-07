import { useState } from 'react';

interface TeamSelectParams {
    onTeamsSelected: (side: "A" | "B", teamId: number, teamName: string) => void;
    teams: { id: number; name: string }[];
}

export function useTeamSelect({ onTeamsSelected, teams }: TeamSelectParams) {
    const [selectedTeams, setSelectedTeams] = useState<number[]>([]);
    const [modalOpen, setModalOpen] = useState(false);

    const handleTeamSelectClick = (teamId: number) => {
        setSelectedTeams(prevSelected => {
            if (prevSelected.includes(teamId)) {
                return prevSelected.filter(id => id !== teamId);
            } else {
                if (prevSelected.length < 2) {
                    return [...prevSelected, teamId];
                } else {
                    return prevSelected;
                }
            }
        });
    }

    const openModal = () => {
        setSelectedTeams([]); // 清空上次的選擇
        setModalOpen(true);
    }

    const closeModal = () => {
        setModalOpen(false);
    }

    const confirmSelection = () => {
        if (selectedTeams.length === 2) {
            closeModal();
            onTeamsSelected("A", selectedTeams[0], teams.find(team => team.id === selectedTeams[0])?.name || "");
            onTeamsSelected("B", selectedTeams[1], teams.find(team => team.id === selectedTeams[1])?.name || "");
        } else {
            // (理論上按鈕被 disabled，不會觸發，但做個保險)
            alert('請剛好選擇兩個隊伍。');
        }
    }

    return {
        selectedTeams,
        modalOpen,
        handleTeamSelectClick,
        openModal,
        closeModal,
        confirmSelection
    };  
}