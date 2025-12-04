"""
URL configuration for API app
"""

from django.urls import path
from . import views

urlpatterns = [
    # Matchup analysis endpoint
    path('matchup/', views.matchup_analysis, name='matchup_analysis'),
    
    # Team rankings prediction endpoint
    path('team_ranking/', views.rankings_prediction, name='rankings_prediction'),
    # Team ranking endpoint
    path('ranking/', views.team_ranking, name='team_ranking'),
    
    # Simulation endpoint (What-If scenarios with trades)
    path('simulation/ranking/', views.simulation_ranking, name='simulation_ranking'),
    
    # Cache status endpoint (for monitoring/debugging)
    path('cache/status/', views.cache_status, name='cache_status'),
]
