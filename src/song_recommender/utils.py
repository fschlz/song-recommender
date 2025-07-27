"""
Utility functions for the DJ Song Recommender application.
"""

import re
from typing import List, Dict, Tuple
from .models import Song


def parse_user_message(message: str) -> Tuple[str, str]:
    """
    Parse user message to extract current song and additional context.
    
    Args:
        message: The user's input message
        
    Returns:
        tuple: (current_song, user_context)
    """
    # Patterns to identify song mentions
    song_patterns = [
        r'(?:playing|now playing|current song is?)\s*["\']?([^"\']+?)["\']?(?:\s+by\s+([^"\']+?))?(?:\s*[,.]|$)',
        r'^["\']?([^"\']+?)["\']?\s*(?:-\s*([^"\']+?))?(?:\s*[,.]|$)',
        r'song[:\s]+["\']?([^"\']+?)["\']?(?:\s+by\s+([^"\']+?))?(?:\s*[,.]|$)',
        r'track[:\s]+["\']?([^"\']+?)["\']?(?:\s+by\s+([^"\']+?))?(?:\s*[,.]|$)'
    ]
    
    current_song = ""
    user_context = message
    
    for pattern in song_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            artist = match.group(2).strip() if match.group(2) else ""
            
            if artist:
                current_song = f"{title} - {artist}"
            else:
                current_song = title
            
            # Remove the song part from the context
            user_context = re.sub(pattern, "", message, flags=re.IGNORECASE).strip()
            break
    
    # If no pattern matched, assume the entire message is the song
    if not current_song:
        # Check if it looks like "Title - Artist" format
        if " - " in message and len(message.split(" - ")) == 2:
            current_song = message.strip()
            user_context = ""
        else:
            # Use first line/sentence as song, rest as context
            lines = message.split('\n', 1)
            current_song = lines[0].strip()
            user_context = lines[1].strip() if len(lines) > 1 else ""
    
    return current_song, user_context


def get_previously_recommended_songs(chat_history: List[Dict], current_song: str) -> List[Song]:
    """
    Extract previously recommended songs from chat history for the same current song.
    
    Args:
        chat_history: The chat history from session state
        current_song: The current song to find recommendations for
        
    Returns:
        List of previously recommended songs for this current song
    """
    previously_recommended = []
    current_song_lower = current_song.lower()
    
    # Find the most recent user message with this current song
    most_recent_user_index = -1
    for i in reversed(range(len(chat_history))):
        if (chat_history[i].get('type') == 'user' and 
            chat_history[i].get('current_song', '').lower() == current_song_lower):
            most_recent_user_index = i
            break
    
    if most_recent_user_index == -1:
        return previously_recommended
    
    # Collect all AI recommendations after that user message
    for i in range(most_recent_user_index + 1, len(chat_history)):
        if chat_history[i].get('type') in ['assistant', 'ai']:
            recommendations = chat_history[i].get('recommendations', [])
            for rec in recommendations:
                if isinstance(rec, dict):
                    previously_recommended.append(Song.from_dict(rec))
    
    return previously_recommended


def format_song_display(song: Song, include_genre: bool = True) -> str:
    """
    Format a song for display in the UI.
    
    Args:
        song: Song object to format
        include_genre: Whether to include genre information
        
    Returns:
        Formatted string representation of the song
    """
    if include_genre and song.genre != "Unknown Genre":
        return f"**{song.title}** by {song.artist} _{song.genre}_"
    else:
        return f"**{song.title}** by {song.artist}"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing/replacing invalid characters.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        Sanitized filename safe for filesystem use
    """
    # Replace invalid characters with underscores
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove any trailing periods or spaces
    sanitized = sanitized.rstrip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"
    
    return sanitized
