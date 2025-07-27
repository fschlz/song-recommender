# 🎧 DJ AI Assistant

An intelligent Streamlit-based DJ assistant that provides AI-powered song recommendations for live DJ sets. The app uses Anthropic's Claude 3.5 Sonnet to suggest the perfect next tracks based on what's currently playing, venue context, energy levels, and your DJ preferences.

## 🎵 Project Concept

The DJ AI Assistant simulates the experience of having an expert DJ mentor by your side during live performances. It understands the flow of a DJ set and provides contextually aware recommendations that maintain energy, complement the current track, and keep the dance floor moving.

### Key Features

- **🤖 AI-Powered Recommendations**: Uses Claude 3.5 Sonnet for intelligent song suggestions
- **💬 Chat Interface**: Conversational interaction where you tell the AI what's currently playing
- **🎛️ Customizable Settings**: Adjust venue type, energy level, similarity, and number of recommendations
- **📝 Context-Aware**: Supports additional DJ guidelines and context in your messages
- **🔄 Re-Recommend**: Get fresh alternatives without duplicates
- **📊 Session Tracking**: Maintains play history and prevents repeated suggestions
- **🧪 Mock Mode**: Test the interface without API calls using curated sample tracks
- **📥 Export History**: Download your complete session history

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- Anthropic API key (for AI recommendations)

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd windsurf-project
   ```

2. **Install dependencies using Poetry**:

   ```bash
   poetry install
   ```

3. **Set up your Anthropic API key** (choose one method):

   **Option A: Environment Variable**

   ```bash
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

   **Option B: Streamlit Secrets**

   ```bash
   mkdir -p .streamlit
   echo 'ANTHROPIC_API_KEY = "your_api_key_here"' > .streamlit/secrets.toml
   ```

   **Option C: Runtime Input**
   - The app will prompt you to enter your API key when you first run it

4. **Run the application**:

   ```bash
   poetry run streamlit run app.py
   ```

5. **Open your browser** to `http://localhost:8501`

### Getting an Anthropic API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in to your account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and use it in your setup

## 🎛️ How to Use

### Basic Workflow

1. **Configure Settings** (in sidebar):
   - **Venue Type**: Club, Festival, Bar, etc.
   - **Energy Level**: Low, Medium, High, Peak
   - **Similarity**: How similar recommendations should be (0.0 - 1.0)
   - **Number of Recommendations**: 1-10 suggestions per request

2. **Start Chatting**:
   - Type the currently playing song: `"Animals - Martin Garrix"`
   - Add context if needed: `"Animals - Martin Garrix; but I want something more melodic"`
   - Press Enter to get AI recommendations

3. **Get More Options**:
   - Click "🔄 Get Different Recommendations" for alternatives
   - Each re-recommend gives fresh suggestions without duplicates

4. **Track Your Set**:
   - View play history in the sidebar
   - Download your session history anytime
   - Songs are automatically added to history when you get recommendations

### Message Format Examples

- **Simple**: `"Levels - Avicii"`
- **With Context**: `"Titanium - David Guetta; but I want something deeper"`
- **With Guidelines**: `"Animals - Martin Garrix and I want to transition to progressive house"`
- **Complex**: `"One More Time - Daft Punk; however the crowd seems tired, let's bring the energy down"`

## 🧠 Recommendation Logic

The DJ AI Assistant uses sophisticated logic to provide contextually appropriate recommendations:

### Input Factors

The AI considers multiple factors when making recommendations:

1. **Currently Playing Song**: The foundation for all recommendations
2. **User Context**: Additional guidelines or preferences from your message
3. **Similarity Level**: Slider setting (0.0 = very different, 1.0 = very similar)
4. **Venue Type & Energy Level**: Environmental context for appropriate suggestions
5. **Play History**: Previously played songs to maintain set coherence
6. **Previous Recommendations**: Songs already suggested for the current track

### Smart Duplicate Prevention

The system implements intelligent duplicate prevention:

- **Per-Song Tracking**: Each current song has its own recommendation history
- **Fresh Start**: New current song = fresh pool of available recommendations
- **Re-Recommend Safety**: Never suggests the same song twice for the same current track
- **Cross-Song Freedom**: Songs can be recommended again for different current tracks

### Example Workflow

```text
1. User: "Animals - Martin Garrix"
   AI: Suggests [Song A, Song B, Song C]

2. User clicks "Re-recommend"
   AI: Suggests [Song D, Song E, Song F] (avoids A, B, C)

3. User: "Levels - Avicii" (new current song)
   AI: Suggests [Song A, Song G, Song H] (A is available again!)

4. User: "Animals - Martin Garrix" (back to first song)
   AI: Suggests [Song I, Song J, Song K] (still avoids A, B, C, D, E, F)
```

### AI Prompt Engineering

The system constructs detailed prompts that include:

- **Current Song Context**: What's playing now
- **DJ Guidelines**: User-provided context and preferences
- **Venue & Energy**: Environmental factors
- **Similarity Instructions**: How similar/different recommendations should be
- **Exclusion Lists**: Songs to avoid (play history + previous recommendations)
- **Output Format**: Structured JSON response with title and artist

## 🛠️ Technical Architecture

### Core Components

- **`app.py`**: Single-file Streamlit application
- **`get_recommendations()`**: Main AI recommendation function
- **`parse_user_message()`**: Extracts current song and context from user input
- **`get_all_recommended_songs_for_current_song()`**: Tracks recommendations per song
- **Session State Management**: Maintains chat history and play history

### Dependencies

- **Streamlit**: Web interface and session management
- **Anthropic**: AI-powered recommendations via Claude 3.5 Sonnet
- **Python-dotenv**: Environment variable management
- **Built-in Logging**: Debug and error tracking

### Mock Mode

For testing and development:

- Toggle "Dev Mode" in sidebar to enable mock recommendations
- Uses curated list of popular electronic/dance tracks
- Implements same duplicate prevention logic as real API mode
- Perfect for testing the interface without API costs

## 🎯 Use Cases

### Live DJ Sets
Get instant recommendations during performances
Maintain energy flow and crowd engagement
Discover new tracks that fit your current vibe

### Set Preparation
Plan track sequences in advance
Explore different musical directions
Build cohesive playlists with AI assistance

### Music Discovery
Find new tracks similar to your favorites
Explore different genres and styles
Build your music library with AI curation

### Learning Tool
Understand track relationships and transitions
Learn about different musical styles and energy levels
Develop your DJ intuition with AI guidance

## 🔧 Configuration Options

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `MOCK_MODE`: Set to "true" to enable mock mode by default

### Streamlit Secrets

```toml
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "your_api_key_here"
```

### Logging

The app uses Python's built-in logging with DEBUG level by default. Logs include:
- API requests and responses
- User interactions and message parsing
- Recommendation filtering and duplicate prevention
- Error handling and debugging information

## 🤝 Contributing

Contributions are welcome! Areas for enhancement:

- Additional music genres and styles
- More sophisticated similarity algorithms
- Integration with music streaming services
- Advanced DJ techniques and transition suggestions
- Mobile-responsive design improvements

## 📄 License

This project is open source. Please check the license file for details.

## 🎵 Enjoy Your Sets

The DJ AI Assistant is designed to enhance your creativity, not replace your artistic vision. Use it as a tool to discover new possibilities, maintain energy flow, and keep your dance floor moving. Happy mixing! 🎧✨