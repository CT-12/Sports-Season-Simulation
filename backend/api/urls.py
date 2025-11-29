"""
URL configuration for API app
"""

from django.urls import path
from . import views

urlpatterns = [
    # Matchup analysis endpoint
    path('matchup/', views.matchup_analysis, name='matchup_analysis'),
]

