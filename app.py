"""
DJ AI Assistant: Song Recommender - A Streamlit application that provides AI-powered song recommendations for DJs

This application allows DJs to get song recommendations based on their current track and set context.
It uses Anthropic's Claude 3.5 Sonnet model to generate intelligent recommendations.

To run this application:
1. Install dependencies: `poetry install`
2. Set up your Anthropic API key in a `.env` file (see `.env.example`).
3. Run the app: `streamlit run app.py`

Note: For development, the app runs in mock mode by default. To use the real Anthropic API,
use the "Dev Mode" toggle in the sidebar or set the MOCK_MODE environment variable to "false".
"""

import streamlit as st
import logging
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv
from src.song_recommender.settings import get_settings
from song_recommender.recommendation_service import RecommendationService
from song_recommender.models import RecommendationRequest

# Load environment variables from .env file
load_dotenv()

# Initialize settings
settings = get_settings()

# --- Logger Setup ---
# Configure logger to display debug messages using centralized settings
logging.basicConfig(level=settings.log_level, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Session State Initialization ---
# Initialize session state for maintaining a list of played songs and their recommendations
if 'play_and_recommendations_history' not in st.session_state:
    logger.debug("Initializing 'play_and_recommendations_history' in session state.")
    st.session_state.play_and_recommendations_history = []

# Initialize mock_mode in session state, defaulting to centralized settings
if 'mock_mode' not in st.session_state:
    initial_mock_mode = settings.mock_mode
    logger.debug(f"Initializing 'mock_mode' in session state to: {initial_mock_mode}")
    st.session_state.mock_mode = initial_mock_mode

# Initialize chat history for the chat interface
if 'chat_history' not in st.session_state:
    logger.debug("Initializing 'chat_history' in session state.")
    st.session_state.chat_history = []

# Initialize settings in session state
if 'venue_type' not in st.session_state:
    st.session_state.venue_type = "Club"
if 'energy_level' not in st.session_state:
    st.session_state.energy_level = "High"
if 'num_recommendations' not in st.session_state:
    st.session_state.num_recommendations = 3
if 'similarity_level' not in st.session_state:
    st.session_state.similarity_level = 0.7
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = settings.default_model

# Initialize recommendation service
recommendation_service = RecommendationService()

# --- Constants ---
# Define constants for venue types and energy levels
VENUE_TYPES = ['Club', 'Wedding', 'Bar', 'Festival', 'Restaurant']
ENERGY_LEVELS = ['Low', 'Medium', 'High', 'Peak']

def get_all_recommended_songs_for_current_song(chat_history: List[Dict], current_song: str) -> List[Dict[str, str]]:
    """
    Extract previously recommended songs from chat history for the same current song to avoid duplicates.
    Only looks at recommendations that came after the most recent user message with the same current song.
    
    Args:
        chat_history (List[Dict]): The chat history from session state
        current_song (str): The current song to find recommendations for
        
    Returns:
        List[Dict[str, str]]: List of previously recommended songs for this current song
    """
    recommendations_for_current_song = []

    # Find the most recent user message with this current song
    last_matching_user_index = -1
    for i in range(len(chat_history) - 1, -1, -1):
        chat = chat_history[i]
        if (chat['type'] == 'user' and
            chat.get('current_song', chat.get('message', '')).strip().lower() == current_song.strip().lower()):
            last_matching_user_index = i
            break

    # If we found a matching user message, collect all AI recommendations after it
    if last_matching_user_index != -1:
        for i in range(last_matching_user_index + 1, len(chat_history)):
            chat = chat_history[i]
            if chat['type'] == 'assistant' and 'recommendations' in chat:
                recommendations_for_current_song.extend(chat['recommendations'])

    logger.debug(f"Found {len(recommendations_for_current_song)} previously recommended songs for current song: '{current_song}'")
    return recommendations_for_current_song

def parse_user_message(message: str) -> tuple[str, str]:
    """
    Parse user message to extract current song and additional context.
    
    Args:
        message (str): The user's input message
        
    Returns:
        tuple[str, str]: (current_song, user_context)
    """
    logger.debug(f"Parsing user message: '{message}'")

    # Define context indicators (transition words and phrases)
    context_indicators = [
        ' but ', ' however ', ' though ', ' although ',
        ' and ', ' also ', ' plus ',
        ' I want ', ' I need ', ' let\'s ', ' we should ',
        ' transition ', ' move ', ' shift ', ' change ', ' evolve ', ' next ',
        ';'  # semicolon as explicit separator
    ]

    # Find the first occurrence of any context indicator
    split_pos = -1
    found_indicator = ""

    for indicator in context_indicators:
        pos = message.lower().find(indicator.lower())
        if pos != -1 and (split_pos == -1 or pos < split_pos):
            split_pos = pos
            found_indicator = indicator

    if split_pos != -1:
        # Split the message at the context indicator
        current_song = message[:split_pos].strip()

        # For semicolon, don't include it in the context
        if found_indicator == ';':
            user_context = message[split_pos + 1:].strip()
        else:
            user_context = message[split_pos + len(found_indicator):].strip()

        logger.debug(f"Parsed - Song: '{current_song}', Context: '{user_context}'")
        return current_song, user_context
    else:
        # No context found, treat entire message as song
        logger.debug(f"No context found - Song: '{message}', Context: ''")
        return message.strip(), ""

def main():
    """Main function that sets up the Streamlit UI and handles user interactions."""
    st.set_page_config(page_title="DJ AI Assistant: Song Recommender", layout="wide")
    st.title("🎧 DJ AI Assistant: Song Recommender")

    # --- Sidebar with Settings, History, and Download ---
    with st.sidebar:
        # API Key Configuration
        st.header("🔑 API Configuration")

        # Check if API key is available using centralized settings
        api_key = settings.effective_api_key

        # Use temporary API key if available
        if not api_key and hasattr(st.session_state, 'temp_api_key'):
            api_key = st.session_state.temp_api_key

        if not api_key:
            st.warning("**Anthropic API Key Required**")
            with st.expander("💡 How to set up your API key", expanded=True):
                st.info("""
                **Option 1: Environment Variable (Recommended)**
                Add to your `.env` file:
                """)
                st.code("ANTHROPIC_API_KEY=your-api-key-here")

                st.info("**Option 2: Temporary Input (This Session Only)**")

            # Temporary API key input
            temp_api_key = st.text_input(
                "Enter API Key (temporary):",
                type="password",
                help="This will only be stored for the current session and will be lost when you refresh the page.",
                placeholder="sk-ant-..."
            )

            if temp_api_key:
                # Store temporarily in session state
                st.session_state.temp_api_key = temp_api_key
                st.success("✅ API key set for this session!")
                st.rerun()
        else:
            # Show API key status
            if hasattr(st.session_state, 'temp_api_key'):
                st.success("✅ Using temporary API key")
                if st.button("Clear temporary API key"):
                    del st.session_state.temp_api_key
                    st.rerun()
            else:
                st.success("✅ Using API key from environment")

        st.divider()
        st.header("⚙️ Settings")

        # DJ Settings
        st.session_state.venue_type = st.selectbox(
            "Venue Type",
            options=VENUE_TYPES,
            index=VENUE_TYPES.index(st.session_state.venue_type)
        )

        st.session_state.energy_level = st.selectbox(
            "Desired Energy Level",
            options=ENERGY_LEVELS,
            index=ENERGY_LEVELS.index(st.session_state.energy_level)
        )

        st.session_state.num_recommendations = st.number_input(
            "Number of Recommendations",
            min_value=1,
            max_value=10,
            value=st.session_state.num_recommendations,
            step=1,
            help="Choose how many song recommendations you want (1-10)"
        )

        st.session_state.similarity_level = st.slider(
            "Similarity Level",
            min_value=0.0,
            max_value=1.0,
            value=st.session_state.similarity_level,
            step=0.1,
            help="Control how similar recommendations should be to the current song (0.0 = very different, 1.0 = very similar)"
        )

        # AI Model Selection
        available_models = [
            "claude-3-5-sonnet-20240620",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-4-sonnet-20250115",
            "claude-4-opus-20250115"
        ]

        st.session_state.selected_model = st.selectbox(
            "AI Model",
            options=available_models,
            index=available_models.index(st.session_state.selected_model) if st.session_state.selected_model in available_models else 0,
            help="Choose which Anthropic Claude model to use for recommendations. Claude 3.5 Sonnet offers the best balance of quality and speed."
        )

        # Dev Mode
        with st.expander("Dev Mode"):
            st.session_state.mock_mode = st.toggle(
                "Enable Mock Mode",
                value=st.session_state.mock_mode,
                help="If enabled, the app returns hardcoded data instead of calling the AI."
            )

        st.divider()

        # Play History Section
        st.header("🎶 Play & Recommendations History")

        if st.session_state.play_and_recommendations_history:
            # Download button for play history
            import json
            history_json = json.dumps(st.session_state.play_and_recommendations_history, indent=2, default=str)
            st.download_button(
                label="💾 Download History",
                data=history_json,
                file_name=f"dj_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Download your play and recommendations history as a JSON file"
            )

            # Display play history
            st.subheader("Last 10 Songs")
            for i, entry in enumerate(st.session_state.play_and_recommendations_history[:10]):  # Show last 5 sessions
                current_song = entry.get('current_song', {})
                recommended_songs = entry.get('recommended_songs', [])

                with st.expander(f"🎵 {current_song.get('title', 'Unknown')} - {current_song.get('artist', 'Unknown')} - {current_song.get('genre', 'Unknown Genre')}"):
                    st.write(f"**Recommendations ({len(recommended_songs)}):**")
                    for j, rec in enumerate(recommended_songs[:10]):  # Show first 10 recommendations
                        st.write(f"  {j+1}. **{rec.get('title', 'Unknown')} - {rec.get('artist', 'Unknown')} - {rec.get('genre', 'Unknown Genre')}**")
                    if len(recommended_songs) > 10:
                        st.caption(f"... and {len(recommended_songs) - 10} more recommendations")

            if len(st.session_state.play_and_recommendations_history) > 10:
                st.caption(f"... and {len(st.session_state.play_and_recommendations_history) - 10} more sessions")

            # Clear history button
            if st.button("🗑️ Clear History", help="Clear all history"):
                st.session_state.play_and_recommendations_history = []
                st.session_state.chat_history = []
                logger.info("Play and recommendations history and chat history cleared by user.")
                st.rerun()
        else:
            st.info("No sessions yet. Start by asking for recommendations!")

    # --- Main Chat Interface ---
    st.header("💬 Chat with DJ AI")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for i, chat in enumerate(st.session_state.chat_history):
            if chat['type'] == 'user':
                with st.chat_message("user"):
                    # Handle both old and new message formats
                    if 'current_song' in chat and 'user_context' in chat:
                        st.write(f"🎵 **Now Playing:** {chat['current_song']}")
                        if chat['user_context']:
                            st.write(f"💬 **Context:** {chat['user_context']}")
                    else:
                        # Fallback for old format
                        st.write(f"🎵 **Now Playing:** {chat['message']}")

                    # Show timestamp
                    if 'timestamp' in chat:
                        timestamp_str = chat['timestamp'].strftime("%H:%M:%S")
                        st.caption(f"⏰ {timestamp_str}")
            else:  # AI response
                with st.chat_message("assistant"):
                    st.write("🎧 **DJ AI Recommendations:**")
                    for rec in chat['recommendations']:
                        # Display in "Title - Artist - Genre" format
                        genre = rec.get('genre', 'Unknown Genre')
                        st.write(f"- **{rec['title']} - {rec['artist']} - {genre}**")

                    # Show timestamp
                    if 'timestamp' in chat:
                        timestamp_str = chat['timestamp'].strftime("%H:%M:%S")
                        st.caption(f"⏰ {timestamp_str}")

                    # Add re-recommend button for the most recent AI response
                    if i == len(st.session_state.chat_history) - 1:
                        if st.button("🔄 Get Different Recommendations", key=f"re_recommend_{i}"):
                            # Find the corresponding user message
                            user_chat = st.session_state.chat_history[i-1] if i > 0 else None
                            if user_chat and user_chat['type'] == 'user':
                                current_song = user_chat.get('current_song', user_chat['message'])
                                user_context = user_chat.get('user_context', '')

                                # Get previously recommended songs for this current song only
                                previously_recommended = get_all_recommended_songs_for_current_song(st.session_state.chat_history, current_song)

                                with st.spinner('🎧 DJ AI is thinking of alternatives...'):
                                    # Create recommendation request
                                    request = RecommendationRequest(
                                        current_song=current_song,
                                        play_history=st.session_state.play_and_recommendations_history,
                                        venue_type=st.session_state.venue_type,
                                        energy_level=st.session_state.energy_level,
                                        num_recommendations=int(st.session_state.num_recommendations),
                                        user_context=user_context,
                                        similarity_level=st.session_state.similarity_level,
                                        previously_recommended=previously_recommended,
                                        model=st.session_state.selected_model
                                    )

                                    # Get effective API key using centralized settings
                                    effective_api_key = settings.effective_api_key
                                    if not effective_api_key and hasattr(st.session_state, 'temp_api_key'):
                                        effective_api_key = st.session_state.temp_api_key

                                    # Create recommendation service with the effective API key
                                    current_recommendation_service = RecommendationService(api_key=effective_api_key)

                                    # Get recommendations using the service
                                    ai_response = current_recommendation_service.get_recommendations(request, mock=st.session_state.mock_mode)

                                    # Extract recommended songs from RecommendationResponse
                                    recommended_songs = [
                                        {
                                            'title': song.title,
                                            'artist': song.artist,
                                            'genre': song.genre
                                        }
                                        for song in ai_response.recommended_songs
                                    ]

                                    # Update play_and_recommendations_history with new recommendations
                                    # Find the existing entry for this current song
                                    current_song_info = {
                                        'title': ai_response.current_song.title,
                                        'artist': ai_response.current_song.artist,
                                        'genre': ai_response.current_song.genre
                                    }

                                    existing_entry = None
                                    for entry in st.session_state.play_and_recommendations_history:
                                        if (entry['current_song'].get('title', '').lower() == current_song_info.get('title', '').lower() and
                                            entry['current_song'].get('artist', '').lower() == current_song_info.get('artist', '').lower()):
                                            existing_entry = entry
                                            break

                                    if existing_entry:
                                        # Add new recommendations to existing entry
                                        existing_entry['recommended_songs'].extend(recommended_songs)
                                    else:
                                        # This shouldn't happen, but create new entry as fallback
                                        st.session_state.play_and_recommendations_history.insert(0, {
                                            'current_song': current_song_info,
                                            'recommended_songs': recommended_songs,
                                            'timestamp': datetime.now()
                                        })

                                    # Add a new AI message instead of overwriting the existing one (create independent copy)
                                    st.session_state.chat_history.append({
                                        'type': 'assistant',
                                        'recommendations': [rec.copy() for rec in recommended_songs],  # Independent copy
                                        'timestamp': datetime.now()
                                    })

                                    logger.info(f"Added new recommendations for: '{current_song}' to both chat and history")
                                    st.rerun()

    # Chat input with helpful placeholder
    user_message = st.chat_input(
        "Enter current song and context (e.g., 'Lose It - FISHER' or 'Animals - Martin Garrix; but let's bring the energy down after')...",
        key="song_input",
    )

    # Show examples in an expander below the input (only when no chat history exists)
    if not st.session_state.chat_history:
        with st.expander("💡 Message Format Examples", expanded=False):
            st.markdown("""
            **Just the song:**
            - `Lose It - FISHER`
            - `Animals - Martin Garrix`
            
            **Song + Context (use transition words like 'but', 'and', 'however'):**
            - `Lose It - FISHER but I want to transition to deeper house`
            - `Animals - Martin Garrix and let's bring the energy down`
            - `Clarity - Zedd; I need to start playing more hip hop soon`
            - `Titanium - David Guetta however we should move toward underground tracks`
            """)

    if user_message:
        # Check if API key is available before processing
        if not api_key:
            st.error("🔑 **Please configure your Anthropic API key in the sidebar before using the chat.**")
            st.stop()

        logger.info(f"Chat message received: '{user_message}'.")

        # Parse the message to extract song and context
        current_song, user_context = parse_user_message(user_message)

        # Add user message to chat history
        st.session_state.chat_history.append({
            'type': 'user',
            'message': user_message,
            'current_song': current_song,
            'user_context': user_context,
            'timestamp': datetime.now()
        })

        # Get previously recommended songs for this current song only
        previously_recommended = get_all_recommended_songs_for_current_song(st.session_state.chat_history, current_song)

        with st.spinner('🎧 DJ AI is thinking...'):
            # Create recommendation request
            request = RecommendationRequest(
                current_song=current_song,
                play_history=st.session_state.play_and_recommendations_history,
                venue_type=st.session_state.venue_type,
                energy_level=st.session_state.energy_level,
                num_recommendations=int(st.session_state.num_recommendations),
                user_context=user_context,
                similarity_level=st.session_state.similarity_level,
                previously_recommended=previously_recommended,
                model=st.session_state.selected_model
            )

            # Get effective API key using centralized settings
            effective_api_key = settings.effective_api_key
            if not effective_api_key and hasattr(st.session_state, 'temp_api_key'):
                effective_api_key = st.session_state.temp_api_key

            # Create recommendation service with the effective API key
            logger.debug(f"Using API key from: {'environment' if settings.anthropic_api_key else 'session state' if effective_api_key else 'none'}")
            current_recommendation_service = RecommendationService(api_key=effective_api_key)

            # Get recommendations using the service
            logger.debug(f"Calling recommendation service with mock={st.session_state.mock_mode}")
            ai_response = current_recommendation_service.get_recommendations(request, mock=st.session_state.mock_mode)
            logger.debug(f"Received response: success={ai_response.success}, num_recommendations={len(ai_response.recommended_songs)}")

            if not ai_response.success:
                logger.error(f"Recommendation service failed: {ai_response.error_message}")
                st.error(f"Failed to get recommendations: {ai_response.error_message}")
                return

            # Extract data from RecommendationResponse object
            current_song_info = {
                'title': ai_response.current_song.title,
                'artist': ai_response.current_song.artist,
                'genre': ai_response.current_song.genre
            }
            recommended_songs = [
                {
                    'title': song.title,
                    'artist': song.artist,
                    'genre': song.genre
                }
                for song in ai_response.recommended_songs
            ]

            # Update play_and_recommendations_history
            # Check if this current song already exists in history
            existing_entry = None
            for entry in st.session_state.play_and_recommendations_history:
                if (entry['current_song'].get('title', '').lower() == current_song_info.get('title', '').lower() and
                    entry['current_song'].get('artist', '').lower() == current_song_info.get('artist', '').lower()):
                    existing_entry = entry
                    break

            if existing_entry:
                # Add new recommendations to existing entry
                existing_entry['recommended_songs'].extend(recommended_songs)
            else:
                # Create new entry
                st.session_state.play_and_recommendations_history.insert(0, {
                    'current_song': current_song_info,
                    'recommended_songs': recommended_songs,
                    'timestamp': datetime.now()
                })

            # Add AI response to chat history (create independent copy to avoid reference sharing)
            st.session_state.chat_history.append({
                'type': 'assistant',
                'recommendations': [rec.copy() for rec in recommended_songs],  # Independent copy
                'timestamp': datetime.now()
            })

            # Note: Play history is now managed through play_and_recommendations_history
            # in the main chat processing logic above

        # Rerun to show the new messages
        st.rerun()

if __name__ == "__main__":
    main()
