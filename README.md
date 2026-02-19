# AiTelegramBot - Media Downloader Bot

A Telegram bot built with aiogram that downloads media content from various platforms using yt-dlp and uploads it to Telegram.

## Features

- 📥 **Media Download**: Download videos and media from various platforms (YouTube, Twitter, Instagram, etc.)
- 💾 **Smart Caching**: Downloaded media is cached for configurable time (default: 1 day) to save bandwidth
- ⚖️ **Size & Duration Limits**: Automatically checks if media fits Telegram's limits before download
- 🔒 **User Whitelist**: Restrict bot access to specific users or groups
- 📊 **Download Queue**: Manages download requests with configurable parallel processing
- 📝 **Comprehensive Logging**: All requests, downloads, and errors are logged with rotation
- 🔄 **Format Conversion**: Automatically converts media to Telegram-supported formats

## Installation

1. Clone the repository:
```bash
git clone https://github.com/WeldonWyman/AiTelegramBot.git
cd AiTelegramBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg (required for yt-dlp):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

4. Create configuration file:
```bash
cp config.example.toml config.toml
```

5. Edit `config.toml` and add your bot token:
```toml
[bot]
token = "YOUR_BOT_TOKEN_FROM_BOTFATHER"
```

## Configuration

The bot is configured via `config.toml` file:

### Bot Settings
- `token`: Your Telegram bot token from @BotFather

### Limits
- `max_file_size_mb`: Maximum file size in MB (default: 50MB, Telegram limit)
- `max_video_duration_seconds`: Maximum video duration in seconds (default: 3600s)

### Cache
- `retention_hours`: How long to keep cached files in hours (default: 24)
- `cache_dir`: Directory to store cached files (default: ./cache)

### Queue
- `max_size`: Maximum number of tasks in queue (default: 10)
- `parallel_workers`: Number of parallel download workers (default: 1)

### Logging
- `log_file`: Path to log file (default: ./bot.log)
- `retention_days`: How many days to keep logs (default: 7)
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Whitelist
- `user_ids`: List of allowed user IDs (empty = allow all)
- `group_ids`: List of allowed group/chat IDs (empty = allow all)

## Usage

### Running Locally

1. Start the bot:
```bash
python bot.py
```

2. In Telegram, start a chat with your bot and use:
   - `/start` - Initialize the bot
   - `/help` - Show help message
   - `/status` - Check queue status
   - Send any media URL to download it

### Running with Docker

1. Build and start the bot:
```bash
docker-compose up -d
```

2. View logs:
```bash
docker-compose logs -f
```

3. Stop the bot:
```bash
docker-compose down
```

### Example URLs Supported
- YouTube: `https://www.youtube.com/watch?v=...`
- Twitter/X: `https://twitter.com/user/status/...`
- Instagram: `https://www.instagram.com/p/...`
- And many more platforms supported by yt-dlp

## Project Structure

```
AiTelegramBot/
├── bot.py              # Main bot implementation
├── config_loader.py    # Configuration loader
├── cache_manager.py    # Cache management
├── downloader.py       # Media downloader using yt-dlp
├── queue_manager.py    # Download queue with parallel processing
├── requirements.txt    # Python dependencies
├── config.example.toml # Example configuration
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## How It Works

1. **User sends URL**: User sends a media URL to the bot
2. **Whitelist check**: Bot verifies user is authorized
3. **Cache check**: Bot checks if media was previously downloaded
4. **Queue management**: If not cached, adds to download queue
5. **Download**: Worker downloads media using yt-dlp
6. **Validation**: Checks file size and duration limits
7. **Format conversion**: Converts to Telegram-compatible format if needed
8. **Upload**: Sends media file to user
9. **Cache**: Stores in cache for future requests

## Logging

All operations are logged to the configured log file with rotation:
- User requests and authorization checks
- Download attempts and results
- Errors and exceptions
- Queue status changes

Log files are automatically rotated when they reach 10MB, and old logs are kept for the configured retention period (default: 7 days).

## Troubleshooting

### Bot doesn't respond
- Check if bot token is correct in `config.toml`
- Verify bot is running without errors in logs
- Check if your user ID is in whitelist (if configured)

### Download fails
- Ensure ffmpeg is installed and in PATH
- Check if URL is supported by yt-dlp
- Verify file size doesn't exceed limits
- Check logs for specific error messages

### "Queue is full" message
- Increase `max_size` in queue configuration
- Increase `parallel_workers` to process downloads faster
- Wait for current downloads to complete

## Security Notes

- Keep your `config.toml` private (contains bot token)
- Use whitelist to restrict bot access
- Be aware of rate limits on hosting platforms
- Monitor disk usage for cache directory

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
