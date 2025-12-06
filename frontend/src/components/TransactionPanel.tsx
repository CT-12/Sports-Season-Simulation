import { useState } from 'react';
import styles from '../styles/TransactionPanel.module.css';

interface TransactionPanelProps {
    transactions: Transaction[];
}

const TransactionPanel = ({ transactions }: TransactionPanelProps) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (transactions.length === 0) {
        return null;
    }

    const toggleExpansion = () => {
        setIsExpanded(!isExpanded);
    };

    return (
        <div className={`${styles.transactionPanel} ${isExpanded ? '' : styles.collapsed}`}>
            <div className={styles.header}>
                <h2>Transactions ({transactions.length})</h2>
                <button onClick={toggleExpansion} className={styles.toggleButton}>
                    {isExpanded ? 'Collapse' : 'Expand'}
                </button>
            </div>
            {isExpanded && (
                <ul>
                    {transactions.map((t, index) => (
                        <li key={index} className={styles.transactionItem}>
                            <span>{t.player_name} ({t.position})</span>
                            <span className={styles.teams}>{t.from_team} → {t.to_team}</span>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default TransactionPanel;

