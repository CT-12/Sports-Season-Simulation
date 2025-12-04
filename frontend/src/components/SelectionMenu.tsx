import React from 'react';
import styles from '../styles/SelectionMenu.module.css';

interface MenuOption {
  label: string;
  value: string;
}

interface MenuGroup {
  title: string;
  options: MenuOption[];
  selectedValue: string;
  onSelect: (value: string) => void;
}

const OptionGroup= ({ title, options, selectedValue, onSelect }: MenuGroup) => (
  <div className={styles.group}>
    <h4 className={styles.groupTitle}>{title}</h4>
    <div className={styles.optionsContainer}>
      {options.map(option => (
        <button
          key={option.value}
          className={`${styles.optionButton} ${selectedValue === option.value ? styles.selected : ''}`}
          onClick={() => onSelect(option.value)}
        >
          {option.label}
        </button>
      ))}
    </div>
  </div>
);


interface SelectionMenuProps {
    mode: 'Team' | 'Player';
    teamStat: string;
    setTeamStat: (stat: string) => void;
    hitterStat: string;
    setHitterStat: (stat: string) => void;
    pitcherStat: string;
    setPitcherStat: (stat: string) => void;
}

const SelectionMenu: React.FC<SelectionMenuProps> = ({
    mode,
    teamStat,
    setTeamStat,
    hitterStat,
    setHitterStat,
    pitcherStat,
    setPitcherStat,
}) => {

    const teamOptions: MenuOption[] = [
        { label: 'Pythagorean', value: 'pythagorean' },
        { label: 'Elo', value: 'elo' },
    ];

    const hitterOptions: MenuOption[] = [
        { label: 'OPS', value: 'ops' },
        { label: 'WAR', value: 'h_war' },
        { label: 'AVG', value: 'avg' },
    ];

    const pitcherOptions: MenuOption[] = [
        { label: 'ERA', value: 'era' },
        { label: 'WAR', value: 'p_war' },
        { label: 'WHIP', value: 'whip' },
    ];

    if (mode === 'Team') {
        return (
            <div className={styles.menuWrapper}>
                <OptionGroup
                    title="Team Stats"
                    options={teamOptions}
                    selectedValue={teamStat}
                    onSelect={setTeamStat}
                />
            </div>
        );
    }

    return (
        <div className={styles.menuWrapper}>
            <OptionGroup
                title="打者"
                options={hitterOptions}
                selectedValue={hitterStat}
                onSelect={setHitterStat}
            />
            <div className={styles.divider}></div>
            <OptionGroup
                title="投手"
                options={pitcherOptions}
                selectedValue={pitcherStat}
                onSelect={setPitcherStat}
            />
        </div>
    );
};

export default SelectionMenu;
