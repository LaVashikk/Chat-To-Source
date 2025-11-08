# Chat2Source

> [!NOTE]
> This project is no longer maintained and is provided as-is.

This project allows streamers and viewers to interact with Source Engine games (Half-Life 2, Portal, Counter-Strike, etc.) through chat commands.

## Features

- **Multi-platform Chat Support**: Connect to YouTube Live and Twitch streams
- **Robust Command Filtering**: Comprehensive filtering system to prevent malicious commands
- **Real-time Web Widget**: Beautiful web interface for displaying chat messages and status
- **Dual Connection Methods**: Support for both NetCon and process hijacking
- **Configurable Settings**: TOML-based configuration with extensive customization options
- **Comprehensive Testing**: Full test suite with pytest
- **Modern Architecture**: Clean, modular design with proper separation of concerns

## Quick Start

### Prerequisites

- Python 3.7 or higher
- A Source Engine game (Half-Life 2, Portal, Counter-Strike, etc.)
- For NetCon: Game must support console access
- For Hijack: Game process must be running

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chat2source
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your settings: Edit settings.toml with your stream URL and preferences

### Basic Usage

1. Start your Source Engine game
2. Run Chat2Source:
```bash
python -m SRC.main --stream-url "YOUR_STREAM_URL" --platform youtube
```
3. Open the web widget at `http://127.0.0.1:5000`
4. Chat commands will now be executed in your game!

## Configuration

### Settings File (`settings.toml`)

```toml
[stream]
platform = "youtube"  # or "twitch"
url = "your_stream_id_or_url"
update_interval = 1.0

[widget]
host = "127.0.0.1"
port = 5000
debug = false

[game]
netcon_host = "127.0.0.1"
netcon_port = 2121
auto_reconnect = true

[logging]
level = "INFO"
```

### Forbidden Commands (`forbidden_config.toml`)

The system includes comprehensive filtering to prevent malicious commands:

- **Forbidden Commands**: Commands that should never be executed
- **Forbidden Entities**: Entity types that shouldn't be spawned
- **Script Filtering**: Block dangerous script commands with exceptions
- **Cvar Limits**: Limit numeric values for console variables

## Architecture

### Core Components

1. **Chat Module** (`SRC/chat/`):
   - `chat_manager.py`: Handles YouTube and Twitch connections
   - `chat_filter.py`: Filters and validates chat commands

2. **Game Module** (`SRC/game/`):
   - `source_bridge.py`: Manages connections to Source Engine games

3. **Widget Module** (`SRC/widget/`):
   - `chat_widget.py`: Flask-based web server for the chat display
   - `static/`: CSS, JavaScript, and other web assets
   - `templates/`: HTML templates

4. **Utilities** (`SRC/utils.py`):
   - Configuration management
   - Helper functions
   - Logging setup

### Connection Methods

#### NetCon (Preferred)
- Uses telnet connection to game console
- Requires game to have NetCon enabled
- More reliable and faster

#### Process Hijacking (Fallback)
- Launches commands via process injection
- Works with any Source Engine game
- Slightly slower but more compatible

## Command Format

Chat commands should be prefixed with `!` or `+`:

- `!noclip` - Toggle noclip mode
- `+forward` - Move forward
- `!say Hello World` - Say message in game
- `!give weapon_crowbar` - Give item

## Security Features

### Command Filtering
- Blacklist dangerous commands (quit, exit, changelevel, etc.)
- Entity spawn filtering
- Script execution protection
- Cvar value limits

### Safe Defaults
- Conservative forbidden command list
- Reasonable cvar limits
- Script exceptions for safe configs

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run specific test file
pytest tests/test_chat.py
```

## Troubleshooting

### Common Issues

1. **"Could not connect to Source Engine game"**
   - Ensure your game is running
   - For NetCon: Enable developer console and NetCon
   - For Hijack: Run as administrator if needed

2. **"Invalid stream URL"**
   - Check your stream URL format
   - For YouTube: Use video ID or full URL
   - For Twitch: Use channel name

3. **"Chat connection lost"**
   - Verify stream is live
   - Check internet connection
   - Ensure correct platform is selected

4. **Commands not executing**
   - Check if commands are in forbidden list
   - Verify game connection status
   - Check console for error messages

### Debug Mode

Enable debug mode in `settings.toml`:

```toml
[widget]
debug = true

[logging]
level = "DEBUG"
```

## Acknowledgments

A special thanks to [damnkrat](https://github.com/damnkrat) for his help with the project.
