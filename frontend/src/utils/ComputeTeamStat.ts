// --- compute team ratings & win probabilities ---
export function computeTeamRating(players: Player[]) {
    let totalRating = 0;
    players.forEach(player => {
        totalRating += player.rating;
    });

    return totalRating;
}

export function computeWinProbability(rosterA: Player[], rosterB: Player[]) {
    const ratingA = computeTeamRating(rosterA);
    const ratingB = computeTeamRating(rosterB);

    const epsilon = 1e-6;
    const totalBoth = ratingA + ratingB + epsilon;
    const probA = ratingA / totalBoth;
    const probB = ratingB / totalBoth;
    return {
        teamAWinProb: Math.round(probA * 10000) / 100,
        teamBWinProb: Math.round(probB * 10000) / 100
    };
}