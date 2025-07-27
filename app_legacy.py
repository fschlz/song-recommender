"""
DJ AI Assistant - A Streamlit application that provides AI-powered song recommendations for DJs

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
import anthropic
import json
import os
import logging
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Logger Setup ---
# Configure logger to display debug messages
logging.basicConfig(level=os.getenv("LOG_LEVEL", "DEBUG"), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

logger.debug("Application starting up.")

# --- Session State Initialization ---
# Initialize session state for maintaining a list of played songs and their recommendations
if 'play_and_recommendations_history' not in st.session_state:
    logger.debug("Initializing 'play_and_recommendations_history' in session state.")
    st.session_state.play_and_recommendations_history = []

# Initialize mock_mode in session state, defaulting to env var or False
if 'mock_mode' not in st.session_state:
    initial_mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"
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
    st.session_state.selected_model = "claude-3-5-sonnet-20240620"

# --- Constants ---
# Define constants for venue types and energy levels
VENUE_TYPES = ['Club', 'Wedding', 'Bar', 'Festival', 'Restaurant']
ENERGY_LEVELS = ['Low', 'Medium', 'High', 'Peak']

def get_recommendations(
    current_song: str,
    play_history: List[Dict[str, str]],
    venue_type: str,
    energy_level: str,
    num_recommendations: int = 3,
    user_context: str = "",
    similarity_level: float = 0.7,
    previously_recommended: List[Dict[str, str]] = None,
    model: str = "claude-3-5-sonnet-20240620",
    mock: bool = True
) -> List[Dict[str, str]]:
    """
    Get song recommendations based on current track and set context.
    
    Args:
        current_song (str): The current song title and artist
        play_history (List[Dict[str, str]]): List of songs already played
        venue_type (str): Type of venue (e.g., Club, Wedding)
        energy_level (str): Desired energy level (e.g., Low, High)
        num_recommendations (int): Number of recommendations to return (1-10)
        user_context (str): Additional context/guidelines from the user about set direction
        similarity_level (float): How similar recommendations should be (0.0-1.0)
        previously_recommended (List[Dict[str, str]]): Songs already recommended to avoid duplicates
        model (str): Anthropic model to use for recommendations (e.g., claude-3-5-sonnet-20240620)
        mock (bool): If True, returns hardcoded recommendations for testing
        
    Returns:
        List[Dict[str, str]]: List of recommended songs with title and artist
    """
    # Handle default parameter
    if previously_recommended is None:
        previously_recommended = []
    
    logger.debug(f"Getting {num_recommendations} recommendations with mock={mock}. User context: '{user_context}'. Excluding {len(previously_recommended)} previous recommendations.")
    
    if mock:
        # Return mock recommendations for testing, avoiding duplicates
        mock_songs = [
            {"title": "Losing It", "artist": "FISHER", "genre": "Tech House"},
            {"title": "Rhyme Dust", "artist": "MK & Dom Dolla", "genre": "Tech House"},
            {"title": "Gecko (Overdrive)", "artist": "Oliver Heldens", "genre": "Future House"},
            {"title": "Mammoth", "artist": "Dimitri Vegas & Like Mike", "genre": "Big Room House"},
            {"title": "Animals", "artist": "Martin Garrix", "genre": "Big Room House"},
            {"title": "Tremor", "artist": "Dimitri Vegas & Like Mike", "genre": "Big Room House"},
            {"title": "Epic", "artist": "Sandro Silva & Quintino", "genre": "Big Room House"},
            {"title": "Spaceman", "artist": "Hardwell", "genre": "Progressive House"},
            {"title": "Tsunami", "artist": "DVBBS & Borgeous", "genre": "Big Room House"},
            {"title": "Clarity", "artist": "Zedd", "genre": "Electro House"},
            {"title": "Bangarang", "artist": "Skrillex", "genre": "Dubstep"},
            {"title": "Levels", "artist": "Avicii", "genre": "Progressive House"},
            {"title": "Titanium", "artist": "David Guetta", "genre": "Electro House"},
            {"title": "Satisfaction", "artist": "Benny Benassi", "genre": "Electro House"},
            {"title": "One More Time", "artist": "Daft Punk", "genre": "French House"}
        ]
        
        # Filter out previously recommended songs
        available_songs = []
        for song in mock_songs:
            is_duplicate = False
            for prev_song in previously_recommended:
                if (song['title'].lower() == prev_song['title'].lower() and 
                    song['artist'].lower() == prev_song['artist'].lower()):
                    is_duplicate = True
                    break
            if not is_duplicate:
                available_songs.append(song)
        
        # Parse current song for mock response
        try:
            title, artist = current_song.rsplit(' - ', 1)
            mock_current_song = {"title": title.strip(), "artist": artist.strip(), "genre": "Electronic"}
        except ValueError:
            mock_current_song = {"title": current_song, "artist": "Unknown Artist", "genre": "Electronic"}
        
        logger.info(f"Returning structured mock response with {num_recommendations} recommendations.")
        return {
            "current_song": mock_current_song,
            "recommended_songs": available_songs[:num_recommendations]
        }
    
    try:
        logger.debug("Initializing Anthropic client.")
        # Securely retrieve API key from Streamlit secrets
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not found in Streamlit secrets.")
            st.error("Anthropic API key is not configured. Please add it to your secrets.")
            return []
            
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construct a detailed prompt for the AI model
        user_context_section = f"\n\n**Additional Context/Guidelines from DJ:**\n{user_context}\n" if user_context.strip() else ""
        
        # Add previously recommended songs section to avoid duplicates
        previously_recommended_section = ""
        if previously_recommended:
            previously_recommended_section = f"\n\n**Songs Already Recommended (DO NOT recommend these again):**\n{json.dumps(previously_recommended, indent=2)}\n"
        
        # Interpret similarity level for the prompt
        if similarity_level >= 0.8:
            similarity_guidance = "very similar in genre, style, and energy"
        elif similarity_level >= 0.6:
            similarity_guidance = "similar in style with some variation"
        elif similarity_level >= 0.4:
            similarity_guidance = "moderately different but complementary"
        elif similarity_level >= 0.2:
            similarity_guidance = "quite different but still cohesive"
        else:
            similarity_guidance = "very different, prioritizing variety and contrast"
        
        prompt = f"""You are a world-class DJ and music expert. Your task is to suggest exactly {num_recommendations} songs to transition to from the current track, based on the provided context.

**Set Context:**
- Venue: {venue_type}
- Desired Energy: {energy_level}
- Similarity Level: {similarity_level:.1f} (recommendations should be {similarity_guidance})

**Current Song:**
- {current_song}

**Songs Already Played in this Set:**
{json.dumps(play_history, indent=2)}{previously_recommended_section}{user_context_section}
Analyze the context, including the current song, play history, venue, desired energy, and similarity preference{', and the DJ\'s additional guidelines' if user_context.strip() else ''}. Suggest songs that are harmonically compatible, maintain a smooth energy flow, and are appropriate for the crowd{'. Pay special attention to any specific directions or preferences mentioned by the DJ' if user_context.strip() else ''}.

IMPORTANT: 
1. The similarity level of {similarity_level:.1f} means your recommendations should be {similarity_guidance} to the current song.
2. NEVER recommend any songs from the "Songs Already Recommended" list - these have been suggested before and should be completely avoided.

Your response MUST be a single, valid JSON object with the following structure:
{
  "current_song": {
    "title": "song title",
    "artist": "artist name",
    "genre": "genre classification"
  },
  "recommended_songs": [
    {
      "title": "song title",
      "artist": "artist name",
      "genre": "genre classification"
    }
  ]
}

For the current_song, parse the provided current song string to extract title and artist, and determine its genre. For recommended_songs, provide exactly {num_recommendations} songs with title, artist, and genre for each. Do not include any text outside of the JSON object.
"""
        
        logger.debug(f"Sending request to Anthropic API using model: {model}")
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        try:
            logger.debug("Successfully received response from AI. Parsing JSON.")
            json_response = json.loads(response.content[0].text)
            
            # Extract structured response
            current_song_info = json_response.get("current_song", {})
            recommended_songs = json_response.get("recommended_songs", [])
            
            logger.info(f"Received structured response: current_song={current_song_info}, {len(recommended_songs)} recommendations")
            
            # Return both current song info and recommendations
            return {
                "current_song": current_song_info,
                "recommended_songs": recommended_songs
            }
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response. Details: {str(e)}")
            st.error(f"Error parsing AI response: {str(e)}")
            return {"current_song": {}, "recommended_songs": []}
            
    except Exception as e:
        logger.error(f"An exception occurred while getting recommendations: {str(e)}")
        st.error(f"Error getting recommendations: {str(e)}")
        return {"current_song": {}, "recommended_songs": []}

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
    st.set_page_config(page_title="DJ AI Assistant", layout="wide")
    st.title("🎧 DJ AI Assistant")
    
    # Check if API key is available
    api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        st.warning("🔑 **Anthropic API Key Required**")
        st.info("""
        To use the DJ AI Assistant, you need to provide your Anthropic API key.
        
        **Option 1: Environment Variable (Recommended)**
        - Add `ANTHROPIC_API_KEY=your_key_here` to your `.env` file
        
        **Option 2: Streamlit Secrets**
        - Add your key to `.streamlit/secrets.toml`:
        ```toml
        ANTHROPIC_API_KEY = "your_key_here"
        ```
        
        **Option 3: Temporary Input (This Session Only)**
        """)
        
        # Temporary API key input
        temp_api_key = st.text_input(
            "Enter your Anthropic API Key (temporary for this session):",
            type="password",
            help="This will only be stored for the current session and will be lost when you refresh the page."
        )
        
        if temp_api_key:
            # Store temporarily in session state
            st.session_state.temp_api_key = temp_api_key
            st.success("✅ API key set for this session! You can now use the DJ AI Assistant.")
            st.rerun()
        else:
            st.stop()  # Stop execution until API key is provided
    
    # Use temporary API key if available
    if not api_key and hasattr(st.session_state, 'temp_api_key'):
        api_key = st.session_state.temp_api_key

    # --- Sidebar with Settings, History, and Download ---
    with st.sidebar:
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
            st.subheader("Recent Sessions")
            for i, entry in enumerate(st.session_state.play_and_recommendations_history[:5]):  # Show last 5 sessions
                current_song = entry.get('current_song', {})
                recommended_songs = entry.get('recommended_songs', [])
                
                with st.expander(f"🎵 {current_song.get('title', 'Unknown')} - {current_song.get('artist', 'Unknown')} ({current_song.get('genre', 'Unknown Genre')})"):
                    st.write(f"**Recommendations ({len(recommended_songs)}):**")
                    for j, rec in enumerate(recommended_songs[:5]):  # Show first 5 recommendations
                        st.write(f"  {j+1}. **{rec.get('title', 'Unknown')}** by {rec.get('artist', 'Unknown')} _{rec.get('genre', 'Unknown Genre')}_")
                    if len(recommended_songs) > 5:
                        st.caption(f"... and {len(recommended_songs) - 5} more recommendations")
            
            if len(st.session_state.play_and_recommendations_history) > 5:
                st.caption(f"... and {len(st.session_state.play_and_recommendations_history) - 5} more sessions")
            
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
            else:  # AI response
                with st.chat_message("assistant"):
                    st.write("🎧 **DJ AI Recommendations:**")
                    for rec in chat['recommendations']:
                        st.write(f"- **{rec['title']}** by {rec['artist']}")
                    
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
                                    ai_response = get_recommendations(
                                        current_song=current_song,
                                        play_history=st.session_state.play_and_recommendations_history,
                                        venue_type=st.session_state.venue_type,
                                        energy_level=st.session_state.energy_level,
                                        num_recommendations=int(st.session_state.num_recommendations),
                                        user_context=user_context,
                                        similarity_level=st.session_state.similarity_level,
                                        previously_recommended=previously_recommended,
                                        model=st.session_state.selected_model,
                                        mock=st.session_state.mock_mode
                                    )
                                    
                                    # Add a new AI message instead of overwriting the existing one
                                    st.session_state.chat_history.append({
                                        'type': 'assistant',
                                        'recommendations': ai_response.get('recommended_songs', []),
                                        'timestamp': datetime.now()
                                    })
                                    
                                    logger.info(f"Added new recommendations for: '{current_song}'")
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
            ai_response = get_recommendations(
                current_song=current_song,
                play_history=st.session_state.play_and_recommendations_history,
                venue_type=st.session_state.venue_type,
                energy_level=st.session_state.energy_level,
                num_recommendations=int(st.session_state.num_recommendations),
                user_context=user_context,
                similarity_level=st.session_state.similarity_level,
                previously_recommended=previously_recommended,
                model=st.session_state.selected_model,
                mock=st.session_state.mock_mode
            )
            
            current_song_info = ai_response.get('current_song', {})
            recommended_songs = ai_response.get('recommended_songs', [])
            
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
            
            # Add AI response to chat history
            st.session_state.chat_history.append({
                'type': 'assistant',
                'recommendations': recommended_songs,
                'timestamp': datetime.now()
            })
            
            # Add to play history
            try:
                title, artist = current_song.rsplit(' - ', 1)
                song_dict = {"title": title.strip(), "artist": artist.strip()}
                logger.debug(f"Adding '{song_dict}' to play history.")
                st.session_state.play_history.insert(0, song_dict)
            except ValueError:
                logger.warning(f"Could not parse song '{current_song}'. Adding as a string.")
                st.session_state.play_history.insert(0, {"title": current_song, "artist": ""})
        
        # Rerun to show the new messages
        st.rerun()

if __name__ == "__main__":
    main()
