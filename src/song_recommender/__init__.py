"""DJ Song Recommender Package

A package for AI-powered song recommendations for DJs.
"""

from .models import Song, RecommendationSession, RecommendationRequest, RecommendationResponse
from .recommendation_service import RecommendationService
from .settings import Settings, get_settings, reload_settings
from .utils import (
    parse_user_message,
    get_previously_recommended_songs,
    format_song_display,
    sanitize_filename
)
from .mock_data import get_mock_recommendations

__version__ = "1.0.0"

__all__ = [
    # Models
    'Song',
    'RecommendationSession', 
    'RecommendationRequest',
    'RecommendationResponse',
    
    # Services
    'RecommendationService',
    
    # Settings
    'Settings',
    'get_settings',
    'reload_settings',
    
    # Utilities
    'parse_user_message',
    'get_previously_recommended_songs',
    'format_song_display',
    'sanitize_filename',
    
    # Mock data
    'get_mock_recommendations'
]