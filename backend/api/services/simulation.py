"""
Simulation Service

Implements the "What-If" simulation pipeline for MLB team rankings.

Pipeline:
1. Fetch: Get the "Base State" from cache (or DB if not cached)
2. Clone: Create a deep copy of the base state in local memory
3. Modify: Apply user's trade transactions to the cloned data
4. Calculate: Run the ranking algorithm on the modified data
5. Return: Send results without persisting anything

This allows users to test trade scenarios without modifying the database.
"""

import copy
import logging
from typing import Dict, List, Optional, Tuple
from .cache_manager import get_base_state
from .team_ranking import (
    rank_teams_from_aggregated_stats,
    get_ranking_with_details_from_aggregated_stats,
    METRIC_DIRECTION,
    TEAM_LEAGUE_MAP,
)

logger = logging.getLogger(__name__)


class SimulationTransaction:
    """Represents a single player trade/transaction."""
    
    def __init__(self, player_name: str, position: str, from_team: str, to_team: str):
        self.player_name = player_name
        self.position = position
        self.from_team = from_team
        self.to_team = to_team
    
    def __repr__(self):
        return (f"SimulationTransaction(player={self.player_name}, "
                f"from={self.from_team}, to={self.to_team})")


def parse_transactions(transactions_data: List[Dict]) -> List[SimulationTransaction]:
    """
    Parse raw transaction data from the API request.
    
    Args:
        transactions_data (List[Dict]): List of transaction dicts from request body
        
    Returns:
        List[SimulationTransaction]: Parsed transaction objects
        
    Raises:
        ValueError: If required fields are missing
    """
    transactions = []
    
    for i, txn_data in enumerate(transactions_data):
        required_fields = ['player_name', 'position', 'from_team', 'to_team']
        missing_fields = [f for f in required_fields if f not in txn_data]
        
        if missing_fields:
            raise ValueError(
                f"Transaction {i}: Missing required fields: {missing_fields}"
            )
        
        transactions.append(SimulationTransaction(
            player_name=txn_data['player_name'],
            position=txn_data['position'],
            from_team=txn_data['from_team'],
            to_team=txn_data['to_team'],
        ))
    
    return transactions


def clone_base_state(base_state: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """
    Create a deep copy of the base state for modification.
    
    This is the "Clone" step in the "Load Once, Clone Many" pattern.
    We need a deep copy to ensure modifications don't affect the cached original.
    
    Args:
        base_state (Dict[str, List[Dict]]): The cached base state
        
    Returns:
        Dict[str, List[Dict]]: A deep copy ready to be modified
    """
    return copy.deepcopy(base_state)


def apply_transactions(
    cloned_state: Dict[str, List[Dict]],
    transactions: List[SimulationTransaction]
) -> Tuple[Dict[str, List[Dict]], List[str]]:
    """
    Apply trade transactions to the cloned state.
    
    This is the "Modify" step. For each transaction:
    1. Find the player in the from_team
    2. Remove from from_team's player list
    3. Add to to_team's player list
    
    Args:
        cloned_state (Dict[str, List[Dict]]): Cloned base state
        transactions (List[SimulationTransaction]): Transactions to apply
        
    Returns:
        Tuple[Dict, List[str]]: Modified state and list of warning/info messages
        
    Raises:
        ValueError: If a player cannot be found or transaction fails
    """
    messages = []
    
    for txn in transactions:
        player_name = txn.player_name
        from_team = txn.from_team
        to_team = txn.to_team
        
        # Validate teams exist in the state
        if from_team not in cloned_state:
            raise ValueError(f"From team not found: {from_team}")
        
        if to_team not in cloned_state:
            raise ValueError(f"To team not found: {to_team}")
        
        # Find the player in from_team
        player_index = None
        player_data = None
        
        for i, player in enumerate(cloned_state[from_team]):
            if player['player_name'].lower() == player_name.lower():
                player_index = i
                player_data = player
                break
        
        if player_index is None:
            raise ValueError(
                f"Player '{player_name}' not found in {from_team}"
            )
        
        # Move the player
        cloned_state[from_team].pop(player_index)
        cloned_state[to_team].append(player_data)
        
        messages.append(
            f"Traded {player_name} from {from_team} to {to_team}"
        )
        logger.info(f"Applied transaction: {txn}")
    
    return cloned_state, messages


def aggregate_stats_from_state(
    state: Dict[str, List[Dict]],
    stat_key: str,
    position_filter: Optional[str] = None
) -> Dict[str, float]:
    """
    Aggregate a specific stat from all teams in the state.
    
    This calculates team-level averages for a given stat metric.
    
    Args:
        state (Dict[str, List[Dict]]): Current simulation state
        stat_key (str): Stat to aggregate (e.g., "avg", "ops", "era")
        position_filter (str): If provided, only include players of this position_type
        
    Returns:
        Dict[str, float]: Team name -> average metric value
    """
    stats = {}
    
    for team_name, players in state.items():
        stat_values = []
        
        for player in players:
            # Try to find stat in hitting stats first, then pitching stats
            hitting_stats = player.get('hitting_stats', {})
            pitching_stats = player.get('pitching_stats', {})
            
            if stat_key in hitting_stats and hitting_stats[stat_key] is not None:
                stat_values.append(float(hitting_stats[stat_key]))
            elif stat_key in pitching_stats and pitching_stats[stat_key] is not None:
                stat_values.append(float(pitching_stats[stat_key]))
        
        # Calculate average (if no values, use 0)
        if stat_values:
            stats[team_name] = sum(stat_values) / len(stat_values)
        else:
            stats[team_name] = 0.0
    
    return stats


def run_simulation(
    hitter_metric: str,
    pitcher_metric: str,
    transactions: List[SimulationTransaction],
    season: int,
    details: bool = False
) -> Dict:
    """
    Run the complete simulation pipeline.
    
    Pipeline:
    1. Fetch base state from cache
    2. Clone the state
    3. Apply transactions
    4. Aggregate stats from modified state
    5. Calculate rankings
    
    Args:
        hitter_metric (str): Hitter metric (e.g., "ops")
        pitcher_metric (str): Pitcher metric (e.g., "era")
        transactions (List[SimulationTransaction]): Trades to apply
        season (int): Season year
        details (bool): If True, include detailed Z-score information
        
    Returns:
        Dict: Ranking results + metadata
        
    Raises:
        ValueError: If metrics are invalid or transactions fail
        Exception: If simulation fails
    """
    # Validate metrics
    if hitter_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown hitter metric: {hitter_metric}")
    if pitcher_metric not in METRIC_DIRECTION:
        raise ValueError(f"Unknown pitcher metric: {pitcher_metric}")
    
    # Step 1: Fetch base state
    logger.info(f"Fetching base state for season {season}...")
    base_state = get_base_state(season)
    
    # Step 2: Clone
    logger.info(f"Cloning base state ({len(base_state)} teams)...")
    cloned_state = clone_base_state(base_state)
    
    # Step 3: Apply transactions
    logger.info(f"Applying {len(transactions)} transactions...")
    try:
        modified_state, txn_messages = apply_transactions(cloned_state, transactions)
    except ValueError as e:
        raise ValueError(f"Transaction failed: {str(e)}")
    
    # Step 4: Aggregate stats from modified state
    logger.info("Aggregating stats from modified state...")
    hitting_stats = aggregate_stats_from_state(modified_state, hitter_metric)
    pitching_stats = aggregate_stats_from_state(modified_state, pitcher_metric)
    
    if not hitting_stats or not pitching_stats:
        raise Exception("Failed to aggregate stats from simulation state")
    
    # Step 5: Calculate rankings
    logger.info("Calculating rankings...")
    try:
        if details:
            result = get_ranking_with_details_from_aggregated_stats(
                hitting_stats,
                pitching_stats,
                hitter_metric,
                pitcher_metric,
                season
            )
        else:
            result = rank_teams_from_aggregated_stats(
                hitting_stats,
                pitching_stats,
                hitter_metric,
                pitcher_metric
            )
    except Exception as e:
        raise Exception(f"Ranking calculation failed: {str(e)}")
    
    # Add simulation metadata
    result["simulation"] = {
        "season": season,
        "hitter_metric": hitter_metric,
        "pitcher_metric": pitcher_metric,
        "transactions_applied": len(transactions),
        "transaction_messages": txn_messages,
        "status": "success"
    }
    
    logger.info("Simulation completed successfully")
    return result
