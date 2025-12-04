"""
API Views for MLB Season Simulator
Provides endpoints for matchup analysis, team rankings prediction, and team ranking
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.matchup import analyze_matchup
from .services.rankings import predict_2026_rankings
from .services.team_ranking import rank_teams_by_metrics, get_ranking_with_details
from .services.simulation import (
    parse_transactions,
    run_simulation,
    SimulationTransaction,
)
from .services.cache_manager import get_cache_info, get_base_state


@api_view(['POST'])
def matchup_analysis(request):
    """
    POST /api/matchup/
    Analyze matchup using specified rating method
    
    Request body:
    {
        "team_A": "Los Angeles Dodgers",
        "team_B": "New York Yankees",
        "method": "Pythagorean"  // or "Elo"
    }
    
    Methods:
    - Pythagorean (default): 2025 data → regression → 2026 prediction + Log5 + Monte Carlo
    - Elo: Latest Elo ratings → Standard Elo win probability
    
    Response format (same for both methods):
    {
        "team_A": [{"id": int, "name": str, "position": str, "Rating": {...}}, ...],
        "team_B": [...],
        "team_A_score": float,
        "team_B_score": float,
        "team_A_win_prob": float,
        "team_B_win_prob": float
    }
    """
    # Validate request data
    team_a = request.data.get('team_A')
    team_b = request.data.get('team_B')
    method = request.data.get('method', 'Pythagorean')  # Default to Pythagorean
    
    if not team_a or not team_b:
        return Response(
            {'error': 'Both team_A and team_B are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate method
    if method not in ['Pythagorean', 'Elo']:
        return Response(
            {'error': 'method must be either "Pythagorean" or "Elo"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Analyze matchup with specified method
    result = analyze_matchup(team_a, team_b, method=method)
    
    if not result:
        error_msg = (
            f'Failed to analyze matchup using {method} method. '
            'Please check team names and ensure required data exists.'
        )
        if method == 'Elo':
            error_msg += ' (Elo ratings must be calculated first using: python manage.py calculate_elo)'
        
        return Response(
            {'error': error_msg},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Debug: Check result before returning
    print(f"[DEBUG] Result keys: {result.keys()}")
    print(f"[DEBUG] Team A count: {len(result.get('team_A', []))}")
    print(f"[DEBUG] Team B count: {len(result.get('team_B', []))}")
    
    return Response(result, status=status.HTTP_200_OK)


@api_view(['POST'])
def rankings_prediction(request):
    """
    POST /api/team_ranking/
    Predict 2026 team rankings by league
    
    Request body:
    {
        "method": "Pythagorean"  // or "Elo"
    }
    
    Response format:
    {
        "NL": ["Los Angeles Dodgers", "Atlanta Braves", ...],
        "AL": ["New York Yankees", "Houston Astros", ...]
    }
    
    Teams are sorted by predicted 2026 strength (best to worst).
    """
    method = request.data.get('method', 'Pythagorean')
    
    # Validate method
    if method not in ['Pythagorean', 'Elo']:
        return Response(
            {'error': 'method must be either "Pythagorean" or "Elo"'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        rankings = predict_2026_rankings(method=method)
        
        if not rankings['NL'] and not rankings['AL']:
            error_msg = f'Failed to calculate rankings using {method} method. Please ensure required data exists.'
            if method == 'Elo':
                error_msg += ' (Elo ratings must be calculated first using: python manage.py calculate_elo)'
            
            return Response(
                {'error': error_msg},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(rankings, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(
            {'error': f'Failed to calculate rankings: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def team_ranking(request):
    """
    POST /api/ranking/
    Rank all MLB teams by a combination of hitter and pitcher metrics.
    
    Request body:
    {
        "hitter_metric": "ops",  // or "avg", "hr", "rbi", etc.
        "pitcher_metric": "era", // or "whip", "so", "w", "l", etc.
        "season": 2025           // optional, defaults to latest season
        "details": false         // optional, set to true for detailed response
    }
    
    Response format (basic):
    {
        "AL": [
            ["New York Yankees", 2.145],
            ["Houston Astros", 1.892],
            ...
        ],
        "NL": [
            ["Los Angeles Dodgers", 2.567],
            ...
        ]
    }
    
    Response format (with details=true):
    {
        "season": 2025,
        "hitter_metric": "ops",
        "pitcher_metric": "era",
        "AL": [
            {
                "rank": 1,
                "team_name": "New York Yankees",
                "score": 2.145,
                "hitter_value": 0.820,
                "pitcher_value": 3.45,
                "hitter_z_score": 1.234,
                "pitcher_z_score": 0.911
            },
            ...
        ],
        "NL": [...]
    }
    """
    # Validate request data
    hitter_metric = request.data.get('hitter_metric')
    pitcher_metric = request.data.get('pitcher_metric')
    season = request.data.get('season')
    details = request.data.get('details', False)  # Request detailed info
    
    if not hitter_metric or not pitcher_metric:
        return Response(
            {
                'error': 'Both hitter_metric and pitcher_metric are required',
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'ops_plus', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'era_plus', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Get ranking
        if details:
            result = get_ranking_with_details(hitter_metric, pitcher_metric, season)
        else:
            result = rank_teams_by_metrics(hitter_metric, pitcher_metric, season)
        
        return Response(result, status=status.HTTP_200_OK)
    
    except ValueError as e:
        return Response(
            {
                'error': str(e),
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'ops_plus', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'era_plus', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {'error': f'Failed to rank teams: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def simulation_ranking(request):
    """
    POST /api/simulation/ranking/
    
    Test "What-If" scenarios by applying trades to a team roster.
    
    This endpoint is STATELESS - no data is persisted. The simulation applies
    trades only to the current request and calculates rankings based on the
    modified rosters.
    
    Uses "Load Once, Clone Many" pattern:
    1. Fetch: Get cached base state (or load from DB if not cached)
    2. Clone: Create in-memory copy of player rosters
    3. Modify: Apply user's trade transactions
    4. Calculate: Run ranking algorithm on modified data
    
    Request body:
    {
        "hitter_metric": "ops",
        "pitcher_metric": "era",
        "season": 2025,
        "details": false,
        "transactions": [
            {
                "player_name": "Shohei Ohtani",
                "position": "DH",
                "from_team": "Los Angeles Dodgers",
                "to_team": "New York Yankees"
            },
            {
                "player_name": "Juan Soto",
                "position": "OF",
                "from_team": "New York Mets",
                "to_team": "Los Angeles Dodgers"
            }
        ]
    }
    
    Response format (similar to /api/ranking/ but with simulation metadata):
    {
        "AL": [...],
        "NL": [...],
        "simulation": {
            "season": 2025,
            "hitter_metric": "ops",
            "pitcher_metric": "era",
            "transactions_applied": 2,
            "transaction_messages": [
                "Traded Shohei Ohtani from Los Angeles Dodgers to New York Yankees",
                "Traded Juan Soto from New York Mets to Los Angeles Dodgers"
            ],
            "status": "success"
        }
    }
    
    Error responses:
    - 400 Bad Request: Missing required fields, invalid metrics, player not found
    - 500 Internal Server Error: Database or calculation errors
    """
    # Extract and validate required fields
    hitter_metric = request.data.get('hitter_metric')
    pitcher_metric = request.data.get('pitcher_metric')
    season = request.data.get('season')
    transactions_data = request.data.get('transactions', [])
    details = request.data.get('details', False)
    
    # Validate basic fields
    if not hitter_metric or not pitcher_metric:
        return Response(
            {
                'error': 'Both hitter_metric and pitcher_metric are required',
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'ops_plus', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'era_plus', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(transactions_data, list):
        return Response(
            {'error': 'transactions must be a list of transaction objects'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(transactions_data) == 0:
        return Response(
            {'error': 'At least one transaction is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Parse transactions
        transactions = parse_transactions(transactions_data)
        
        # Run simulation
        result = run_simulation(
            hitter_metric=hitter_metric,
            pitcher_metric=pitcher_metric,
            transactions=transactions,
            season=season,
            details=details
        )
        
        return Response(result, status=status.HTTP_200_OK)
    
    except ValueError as e:
        # Validation errors (invalid metrics, player not found, missing fields)
        return Response(
            {
                'error': str(e),
                'available_metrics': {
                    'hitting': ['avg', 'ops', 'ops_plus', 'hr', 'rbi', 'r', 'h', 'obp', 'slg'],
                    'pitching': ['era', 'era_plus', 'whip', 'so', 'w', 'l', 'bb']
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        # Database or calculation errors
        return Response(
            {'error': f'Simulation failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def cache_status(request):
    """
    GET /api/cache/status/?season=2025
    
    Get information about the current cache state for debugging/monitoring.
    
    Query parameters:
    - season (int, optional): Season to check. Defaults to 2025.
    
    Response format:
    {
        "season": 2025,
        "cache_key": "mlb_players_base_state_2025",
        "is_cached": true,
        "cached_teams": 30,
        "cached_players": 1234,
        "cache_ttl": 3600
    }
    """
    season = request.query_params.get('season', 2025)
    
    try:
        season = int(season)
    except ValueError:
        return Response(
            {'error': 'season must be an integer'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        cache_info = get_cache_info(season)
        return Response(cache_info, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': f'Failed to get cache info: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
