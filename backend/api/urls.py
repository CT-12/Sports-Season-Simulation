"""
URL configuration for API app
"""

from django.urls import path
from . import views

urlpatterns = [
    # Matchup analysis endpoint
    path('matchup/', views.matchup_analysis, name='matchup_analysis'),
    
    # Team ranking endpoint
    path('ranking/', views.team_ranking, name='team_ranking'),
]

