"""
Data models for the DJ AI Assistant.

This module contains the core data structures using Pydantic for validation,
including Song, RecommendationSession, and request/response models.
"""

from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field, validator


class Song(BaseModel):
    """Represents a song with title, artist, and genre."""
    title: str = Field(..., min_length=1, description="Song title")
    artist: str = Field(..., min_length=1, description="Artist name")
    genre: str = Field(..., min_length=1, description="Music genre")

    @validator('title', 'artist', 'genre')
    def validate_non_empty_strings(cls, v):
        """Ensure strings are not empty or just whitespace."""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace')
        return v.strip()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Song':
        """Create a Song from a dictionary with validation."""
        return cls(
            title=data.get('title', ''),
            artist=data.get('artist', ''),
            genre=data.get('genre', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Song to dictionary."""
        return self.model_dump()


class RecommendationSession(BaseModel):
    """Represents a session with a current song and its recommendations."""
    current_song: Song = Field(..., description="The currently playing song")
    recommended_songs: List[Song] = Field(default=[], description="List of recommended songs")
    timestamp: datetime = Field(default_factory=datetime.now, description="Session timestamp")

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary format."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict) -> "RecommendationSession":
        """Create RecommendationSession from dictionary."""
        return cls(
            current_song=Song.from_dict(data.get("current_song", {})),
            recommended_songs=[Song.from_dict(song) for song in data.get("recommended_songs", [])],
            timestamp=data.get("timestamp", datetime.now())
        )


class RecommendationRequest(BaseModel):
    """Request parameters for getting recommendations."""
    current_song: str = Field(..., min_length=1, description="Currently playing song")
    venue_type: str = Field(..., description="Type of venue (Club, Wedding, etc.)")
    energy_level: str = Field(..., description="Desired energy level (Low, Medium, High, Peak)")
    num_recommendations: int = Field(default=3, ge=1, le=10, description="Number of recommendations")
    user_context: str = Field(default="", description="Additional context from user")
    similarity_level: float = Field(default=0.7, ge=0.0, le=1.0, description="Similarity level (0.0-1.0)")
    previously_recommended: List[Song] = Field(default=[], description="Previously recommended songs to exclude")
    model: str = Field(default="claude-3-5-sonnet-20240620", description="Anthropic model to use")

    @validator('current_song')
    def validate_current_song(cls, v):
        """Ensure current song is not empty."""
        if not v or not v.strip():
            raise ValueError('Current song cannot be empty')
        return v.strip()


class RecommendationResponse(BaseModel):
    """Response containing current song info and recommendations."""
    current_song: Song = Field(..., description="The current song information")
    recommended_songs: List[Song] = Field(default=[], description="List of recommended songs")
    success: bool = Field(default=True, description="Whether the recommendation was successful")
    error_message: str = Field(default="", description="Error message if unsuccessful")

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format."""
        return self.model_dump()
