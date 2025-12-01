import React from 'react';
import styles from '../styles/UISlider.module.css';

interface UISliderProps {
  options: string[];
  selected: string;
  onChange: (selected: string) => void;
}

const UISlider = ({ options, selected, onChange }: UISliderProps) => {
  const selectedIndex = options.indexOf(selected);
  return (
    <div className={styles.sliderContainer} style={{'--options': options.length} as React.CSSProperties}>
      {options.map((option) => (
        <button
          key={option}
          className={`${styles.sliderOption} ${selected === option ? styles.selected : ''}`}
          onClick={() => onChange(option)}
        >
          {option}
        </button>
      ))}
      <div className={styles.sliderThumb} style={{'--selected-index': selectedIndex} as React.CSSProperties} />
    </div>
  );
};

export default UISlider;
