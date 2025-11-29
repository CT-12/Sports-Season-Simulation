"""
API Views for MLB Season Simulator
Provides endpoint for matchup analysis with Pythagorean or Elo rating methods
"""

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services.matchup import analyze_matchup


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
        "team_A": [{"id": int, "name": str, "position": str, "score": float}, ...],
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
    
    return Response(result, status=status.HTTP_200_OK)

