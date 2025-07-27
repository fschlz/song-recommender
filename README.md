# 🎧 DJ AI Assistant

A professional Streamlit-based DJ assistant that provides AI-powered song recommendations for live DJ sets. Built with modern software engineering practices, the app uses Anthropic's Claude models to suggest contextually perfect next tracks based on what's currently playing, venue atmosphere, energy flow, and your personal DJ style.

## 🎵 Project Overview

The DJ AI Assistant acts as your intelligent mixing companion, understanding the nuances of DJ set flow and providing expert-level recommendations that maintain energy, complement harmonic progressions, and keep the dance floor engaged. Whether you're performing at intimate venues or large festivals, the AI adapts to your context and preferences.

## ✨ Key Features

### 🤖 **AI-Powered Intelligence**

- **Multiple Claude Models**: Choose from Claude 3.5 Sonnet and other Anthropic models
- **Context-Aware Recommendations**: Understands venue, energy, and musical flow
- **Smart Duplicate Prevention**: Never suggests the same song twice per current track
- **Harmonic Compatibility**: Considers musical key relationships and energy transitions

### 💬 **Interactive Chat Interface**

- **Natural Conversation**: Simply tell the AI what's currently playing
- **Contextual Guidelines**: Add specific instructions or preferences to each request
- **Separate Message History**: Each recommendation request creates a distinct chat message
- **Persistent Chat Log**: Full conversation history maintained throughout your session

### 🎛️ **Professional DJ Controls**

- **Venue Type Selection**: Club, Festival, Lounge, Wedding, and more
- **Energy Level Control**: Build up, maintain, or bring down the energy
- **Similarity Slider**: Fine-tune how similar or different recommendations should be
- **Recommendation Count**: Choose 1-10 suggestions per request
- **Model Selection**: Pick your preferred Claude model for different recommendation styles

### 📊 **Session Management**

- **Comprehensive History**: Track all played songs and their recommendations with genres
- **Smart Re-Recommendations**: Get fresh alternatives while avoiding previous suggestions
- **Download History**: Export your complete session as JSON for later reference
- **Last 10 Songs Display**: Quick sidebar view of recent tracks and recommendations

### 🔧 **Developer & Testing Features**

- **Mock Mode**: Test the interface without API calls using curated sample tracks
- **Flexible API Key Input**: Use environment variables or temporary UI input
- **Debug Logging**: Comprehensive logging for troubleshooting and development
- **Clean Architecture**: Modular codebase with proper separation of concerns

## 🏗️ Technical Architecture

The DJ AI Assistant is built with modern software engineering practices, featuring a clean modular architecture that separates concerns and enables easy testing and maintenance.

### Project Structure

```text
src/song_recommender/
├── __init__.py              # Package initialization and exports
├── models.py                # Pydantic data models (Song, RecommendationRequest, etc.)
├── recommendation_service.py # Core AI recommendation business logic
├── mock_data.py            # Sample data for testing and mock mode
├── utils.py                # Utility functions for parsing and formatting
└── settings.py             # Configuration management with pydantic-settings

app.py                      # Main Streamlit application (400 lines)
app_legacy.py              # Original monolithic version (archived)
requirements.txt           # Python dependencies
pyproject.toml            # Poetry configuration
.env                      # Environment variables (API keys, settings)
README.md                # This documentation
```

### Key Design Principles

- **Separation of Concerns**: UI logic separated from business logic
- **Dependency Injection**: Services properly injected for testability
- **Type Safety**: Full type hints with Pydantic models for validation
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Logging**: Structured logging with configurable levels
- **Configuration Management**: Environment-based configuration with validation

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Poetry (for dependency management)
- Anthropic API key (for AI recommendations)

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/fschlz/song-recommender.git
   cd song-recommender
   ```

2. **Install dependencies using Poetry**:

   ```bash
   poetry install
   ```

3. **Set up your Anthropic API key** (choose one method):

   **Option A: Environment Variable (.env file)**

   ```bash
   echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
   ```

   **Option B: Streamlit Secrets**

   ```bash
   mkdir -p .streamlit
   echo 'ANTHROPIC_API_KEY = "your_api_key_here"' > .streamlit/secrets.toml
   ```

   **Option C: Runtime Input (Recommended for Testing)**
   - Leave the .env file empty or commented out
   - The app will provide a sidebar input field for temporary API key entry
   - Perfect for testing without committing API keys to files

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

## 🎯 Use Cases

### Live DJ Sets
- Get instant recommendations during performances
- Maintain energy flow and crowd engagement
- Adapt to venue atmosphere and crowd response
- Build cohesive sets with harmonic compatibility

### Practice Sessions
- Explore new music combinations
- Learn about genre transitions and mixing techniques
- Build confidence with AI-assisted track selection
- Experiment with different energy progressions

### Music Discovery
- Find new tracks similar to your favorites
- Explore different genres and subgenres
- Discover artists you might not have found otherwise
- Build playlists for different moods and venues

### Event Planning
- Prepare track lists for specific venue types
- Plan energy progression for different event phases
- Create backup options for different crowd responses
- Develop signature sound and style

## 🐛 Troubleshooting

### Common Issues

**API Key Not Working**
- Verify your Anthropic API key is correct
- Check that you have sufficient API credits
- Ensure the key is properly set in `.env` or entered in the sidebar
- Look for error messages in the Streamlit interface

**No Recommendations Appearing**
- Check your internet connection
- Verify the API key is valid and has credits
- Try enabling Mock Mode to test the interface
- Check the browser console for JavaScript errors

**Duplicate Recommendations**
- This should not happen - if it does, please report it as a bug
- Try clearing your session state by refreshing the page
- Check that the current song format is correct ("Title - Artist")

**Performance Issues**
- Reduce the number of recommendations per request
- Check your internet connection speed
- Consider using Mock Mode for testing

### Debug Mode

Enable debug logging by setting the log level in your environment:

```bash
echo "LOG_LEVEL=DEBUG" >> .env
```

This will show detailed information about API calls, parsing, and internal operations.

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Install dependencies: `poetry install`
4. Make your changes
5. Test thoroughly with both real API and Mock Mode
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints throughout the codebase
- Add comprehensive docstrings for all functions
- Maintain the modular architecture with proper separation of concerns
- Write unit tests for new functionality

### Areas for Contribution

- **New AI Models**: Add support for other LLM providers
- **Music Analysis**: Integrate with music analysis APIs for key/BPM matching
- **Playlist Integration**: Connect with Spotify, Apple Music, or other platforms
- **Advanced Filtering**: Add more sophisticated recommendation filters
- **UI Improvements**: Enhance the Streamlit interface
- **Testing**: Expand test coverage and add integration tests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Anthropic** for providing the Claude AI models
- **Streamlit** for the excellent web framework
- **The DJ Community** for inspiration and feedback
- **Contributors** who help improve this project

## 📞 Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [GitHub Issues](https://github.com/fschlz/song-recommender/issues)
3. Create a new issue with detailed information
4. Join our community discussions

---

**Made with ❤️ for the DJ community**

*Keep the dance floor moving! 🎵*
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