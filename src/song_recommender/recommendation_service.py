"""
Recommendation service for the DJ AI Assistant.

This module handles both AI-powered and mock recommendations,
including prompt construction, API calls, and response parsing.
Now uses Pydantic for enhanced JSON parsing and validation.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from pydantic import ValidationError

from .models import RecommendationRequest, RecommendationResponse, Song
from .mock_data import get_mock_recommendations
from .settings import get_settings

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for handling song recommendations with Pydantic validation."""

    _api_key_warning_logged = False

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the recommendation service with settings."""
        self.settings = get_settings()
        self.client = None
        effective_api_key = api_key or self.settings.effective_api_key

        if effective_api_key:
            try:
                self.client = Anthropic(api_key=effective_api_key)
                logger.debug("Anthropic client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
        elif not RecommendationService._api_key_warning_logged:
            logger.warning("No API key available. Only mock mode will be available.")
            RecommendationService._api_key_warning_logged = True

    def _get_similarity_guidance(self, similarity_level: str) -> str:
        """Convert categorical similarity level to descriptive guidance text."""
        similarity_map = {
            "Very similar": "very similar in genre, style, and energy",
            "Similar with variation": "similar in style with some variation",
            "Moderately different": "moderately different but complementary",
            "Quite different": "quite different but still cohesive",
            "Very different": "very different, prioritizing variety and contrast"
        }
        return similarity_map.get(similarity_level, "similar in style with some variation")

    def _load_and_format_prompt(self, request: RecommendationRequest) -> str:
        """Load the prompt from a file and format it with request data."""
        try:
            prompt_path = Path(__file__).parent / "prompts" / "prompt_template.txt"
            prompt_template = prompt_path.read_text()

            user_context_section = f"\nUser's additional context: {request.user_context}" if request.user_context else ""

            previously_recommended_section = ""
            if request.previously_recommended:
                prev_songs_list = "\n".join([f"- {song.title} by {song.artist}" for song in request.previously_recommended])
                previously_recommended_section = (
                    "\n\nDo NOT recommend any of these songs that were previously suggested for this current song:\n"
                    f"{prev_songs_list}"
                )

            similarity_guidance = self._get_similarity_guidance(request.similarity_level)
            return prompt_template.format(
                current_song=request.current_song,
                num_recommendations=request.num_recommendations,
                venue_type=request.venue_type,
                desired_energy_level=request.energy_level,
                similarity_level=request.similarity_level,
                similarity_guidance=similarity_guidance,
                user_context_section=user_context_section,
                previously_recommended_section=previously_recommended_section,
            )
        except FileNotFoundError:
            logger.error("Recommendation prompt file not found.")
            return ""
        except Exception as e:
            logger.error(f"Error loading or formatting prompt: {e}")
            return ""

    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """Get song recommendations based on the request."""
        if self.settings.mock_mode:
            logger.info(f"Using mock recommendations for '{request.current_song}'.")
            return get_mock_recommendations(request)

        if not self.client:
            return RecommendationResponse(
                current_song=self._parse_current_song(request.current_song),
                recommended_songs=[],
                success=False,
                error_message="Anthropic client is not initialized. Check API key.",
            )

        system_prompt = self._load_and_format_prompt(request)
        logger.debug(f"Formatted prompt for LLM API:\n{system_prompt}")
        if not system_prompt:
            return RecommendationResponse(
                current_song=self._parse_current_song(request.current_song),
                recommended_songs=[],
                success=False,
                error_message="Failed to load or format the recommendation prompt.",
            )

        try:
            logger.debug(f"Calling Anthropic API for model: {request.model}")
            message = self.client.messages.create(
                model=request.model,
                max_tokens=self.settings.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": f"Give me {request.num_recommendations} song recommendations. TIA!"}],
            )

            ai_response_text = message.content[0].text
            logger.debug(f"Raw AI Response:\n{ai_response_text}")

            cleaned_response = ai_response_text.strip().replace("```json", "").replace("```", "").strip()

            try:
                response_data = json.loads(cleaned_response)
                current_song_data = response_data.get("current_song", {})
                recommended_songs_data = response_data.get("recommended_songs", [])

                current_song = Song.model_validate(current_song_data)
                recommended_songs = [Song.model_validate(song) for song in recommended_songs_data]

                return RecommendationResponse(current_song=current_song, recommended_songs=recommended_songs, success=True)

            except ValidationError as e:
                logger.error(f"Pydantic validation failed for AI response: {e}")
                return RecommendationResponse(
                    current_song=self._parse_current_song(request.current_song),
                    recommended_songs=[],
                    success=False,
                    error_message=f"Invalid song data from AI: {e}",
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return RecommendationResponse(
                current_song=self._parse_current_song(request.current_song),
                recommended_songs=[],
                success=False,
                error_message=f"Invalid JSON response from AI: {e}",
            )
        except Exception as e:
            logger.error(f"Error calling Anthropic API: {e}")
            return RecommendationResponse(
                current_song=self._parse_current_song(request.current_song),
                recommended_songs=[],
                success=False,
                error_message=f"API error: {e}",
            )

    def _parse_current_song(self, current_song_input: str) -> Song:
        """Parse current song input to extract title and artist."""
        if " - " in current_song_input:
            parts = current_song_input.rsplit(" - ", 1)
            title = parts[0].strip()
            artist = parts[1].strip() if len(parts) > 1 else "Unknown Artist"
        else:
            title = current_song_input.strip()
            artist = "Unknown Artist"

        return Song(title=title, artist=artist, genre="Unknown Genre")
