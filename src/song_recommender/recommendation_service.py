"""
Recommendation service for the DJ AI Assistant.

This module handles both AI-powered and mock recommendations,
including prompt construction, API calls, and response parsing.
Now uses Pydantic for enhanced JSON parsing and validation.
"""

import json
import logging
from typing import List, Optional
from anthropic import Anthropic
from pydantic import ValidationError

from .models import Song, RecommendationRequest, RecommendationResponse
from .mock_data import get_mock_recommendations
from .settings import get_settings

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for handling song recommendations with Pydantic validation."""
    
    # Class-level flag to prevent repeated API key warnings
    _api_key_warning_logged = False
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the recommendation service with settings."""
        self.settings = get_settings()
        self.client = None
        
        # Use provided API key or get from settings
        effective_api_key = api_key or self.settings.effective_api_key
        
        if effective_api_key:
            try:
                self.client = Anthropic(api_key=effective_api_key)
                logger.debug("Anthropic client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        else:
            # Only log the warning once to prevent terminal flooding
            if not RecommendationService._api_key_warning_logged:
                logger.warning("No API key available. Only mock mode will be available.")
                RecommendationService._api_key_warning_logged = True
    
    def get_recommendations(self, request: RecommendationRequest, mock: bool = False) -> RecommendationResponse:
        """
        Get song recommendations based on the request parameters.
        
        Args:
            request: RecommendationRequest containing all parameters
            mock: If True, returns mock data instead of calling AI
            
        Returns:
            RecommendationResponse with current song and recommendations
        """
        if mock:
            return self._get_mock_recommendations(request)
        
        if not self.client:
            return RecommendationResponse(
                current_song=Song(title="Unknown", artist="Unknown", genre="Unknown"),
                recommended_songs=[],
                success=False,
                error_message="Anthropic API key not configured"
            )
        
        try:
            return self._get_ai_recommendations(request)
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return RecommendationResponse(
                current_song=Song(title="Unknown", artist="Unknown", genre="Unknown"),
                recommended_songs=[],
                success=False,
                error_message=str(e)
            )
    
    def _get_mock_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get mock recommendations for testing."""
        logger.info("Using mock mode for recommendations.")
        
        # Parse current song
        current_song = self._parse_current_song(request.current_song)
        
        # Get mock recommendations
        mock_songs = get_mock_recommendations()
        
        # Filter out previously recommended songs
        previously_recommended_titles = {song.title.lower() for song in request.previously_recommended}
        available_songs = [song for song in mock_songs 
                          if song.title.lower() not in previously_recommended_titles]
        
        # Select requested number of recommendations
        selected_songs = available_songs[:request.num_recommendations]
        
        return RecommendationResponse(
            current_song=current_song,
            recommended_songs=selected_songs,
            success=True
        )
    
    def _get_ai_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get recommendations from AI."""
        logger.info(f"Getting AI recommendations using model: {request.model}")
        
        # Build context for previously recommended songs
        prev_songs_context = ""
        if request.previously_recommended:
            prev_songs_list = [f"- {song.title} by {song.artist}" for song in request.previously_recommended]
            prev_songs_context = f"""
            
Do NOT recommend any of these songs that were previously suggested for this current song:
{chr(10).join(prev_songs_list)}"""
        
        # Create the prompt
        prompt = f"""You are a professional DJ AI assistant. A DJ is playing "{request.current_song}" and needs {request.num_recommendations} song recommendations for their set.

Context:
- Venue: {request.venue_type}
- Energy Level: {request.energy_level}
- Similarity Level: {request.similarity_level} (0.0 = very different, 1.0 = very similar)
- Additional Context: {request.user_context or "None"}
{prev_songs_context}

Return your response as a JSON object with this EXACT structure:
{{
    "current_song": {{
        "title": "parsed title from input",
        "artist": "parsed artist from input", 
        "genre": "identified genre"
    }},
    "recommended_songs": [
        {{
            "title": "Song Title",
            "artist": "Artist Name",
            "genre": "Genre"
        }}
    ]
}}

Parse the current song from the input "{request.current_song}" and identify its genre. Then provide {request.num_recommendations} diverse recommendations that match the venue type, energy level, and similarity preferences. Include accurate genre information for all songs.

Respond with ONLY the JSON object, no additional text."""

        try:
            response = self.client.messages.create(
                model=request.model,
                max_tokens=self.settings.max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = response.content[0].text
            logger.debug(f"AI response: {response_text}")
            
            # Parse JSON response using Pydantic validation
            try:
                response_data = json.loads(response_text)
                
                # Extract and validate current song and recommendations using Pydantic
                current_song_data = response_data.get("current_song", {})
                recommended_songs_data = response_data.get("recommended_songs", [])
                
                current_song = Song.model_validate(current_song_data)
                recommended_songs = [Song.model_validate(song) for song in recommended_songs_data]
                
                return RecommendationResponse(
                    current_song=current_song,
                    recommended_songs=recommended_songs,
                    success=True
                )
                
            except ValidationError as e:
                logger.error(f"Pydantic validation failed for AI response: {e}")
                return RecommendationResponse(
                    current_song=Song(title="Unknown", artist="Unknown", genre="Unknown"),
                    recommended_songs=[],
                    success=False,
                    error_message=f"Invalid song data from AI: {e}"
                )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return RecommendationResponse(
                current_song=Song(title="Unknown", artist="Unknown", genre="Unknown"),
                recommended_songs=[],
                success=False,
                error_message=f"Invalid JSON response from AI: {e}"
            )
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return RecommendationResponse(
                current_song=Song(title="Unknown", artist="Unknown", genre="Unknown"),
                recommended_songs=[],
                success=False,
                error_message=f"API error: {e}"
            )
    
    def _parse_current_song(self, current_song_input: str) -> Song:
        """Parse current song input to extract title and artist."""
        # Try to split by " - " to separate title and artist
        if " - " in current_song_input:
            parts = current_song_input.rsplit(" - ", 1)  # Split from the right to handle titles with " - "
            title = parts[0].strip()
            artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"
        else:
            title = current_song_input.strip()
            artist = "Unknown Artist"
        
        return Song(title=title, artist=artist, genre="Unknown Genre")
