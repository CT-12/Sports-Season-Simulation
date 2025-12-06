const getUniqueTransactions = (list: Transaction[]): Transaction[] => {
	const map = new Map<string, Transaction>();

	list.forEach((item) => {
		// 建立唯一識別碼 (Composite Key)
		// 建議中間加個分隔符號如 '|' 避免極端情況下的字串沾黏
		const key = `${item.player_name}|${item.position}|${item.from_team}`;
		
		// Map 的特性：重複的 Key 會被後面的覆蓋 -> 自動保留最後一筆
		map.set(key, item);
	});

	// 將 Map 的 Values 轉回陣列
	return Array.from(map.values());
};

export { getUniqueTransactions };