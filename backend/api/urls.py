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
]

