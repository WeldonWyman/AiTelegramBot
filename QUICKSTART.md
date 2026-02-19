# Quick Start Guide

This guide will help you get the bot up and running quickly.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- ffmpeg (for video processing)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install ffmpeg

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Download from https://ffmpeg.org/download.html and add to PATH.

### 3. Create Configuration File

```bash
cp config.example.toml config.toml
```

### 4. Get Your Bot Token

1. Open Telegram and search for @BotFather
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token you receive

### 5. Configure the Bot

Edit `config.toml` and update the token:

```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token
```

### 6. (Optional) Configure Whitelist

If you want to restrict access to specific users:

```toml
[whitelist]
user_ids = [123456789]  # Your Telegram user ID
group_ids = []  # Or specific group IDs
```

To find your user ID:
- Send a message to @userinfobot on Telegram
- Or leave empty to allow all users

### 7. Run Tests (Optional)

```bash
python test_bot.py
```

### 8. Start the Bot

```bash
python bot.py
```

You should see:
```
2024-02-19 10:00:00 - __main__ - INFO - Bot initialized successfully
2024-02-19 10:00:00 - __main__ - INFO - Starting bot...
2024-02-19 10:00:00 - __main__ - INFO - Bot is running...
```

### 9. Test the Bot

1. Open Telegram and find your bot
2. Send `/start` command
3. Send a video URL (e.g., YouTube link)
4. Wait for the bot to download and send the video

## Example URLs to Test

- YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- Twitter: `https://twitter.com/user/status/123456`
- Instagram: `https://www.instagram.com/p/ABC123/`

## Troubleshooting

### "ModuleNotFoundError: No module named 'aiogram'"
Run: `pip install -r requirements.txt`

### "Token is invalid!"
Check that you've correctly copied the token from @BotFather to config.toml

### "You are not authorized to use this bot"
Add your user ID to the whitelist in config.toml, or leave user_ids empty

### Download fails
- Check if ffmpeg is installed: `ffmpeg -version`
- Check the logs in `bot.log` for detailed error messages
- Ensure the URL is from a supported platform

## Running in Production

For production deployment, consider:

1. **Use systemd service** (Linux):
   Create `/etc/systemd/system/telegram-bot.service`

2. **Use PM2** (Node.js process manager works for Python too):
   ```bash
   pm2 start bot.py --name telegram-bot --interpreter python3
   ```

3. **Use Docker**:
   Create a Dockerfile and run in a container

4. **Monitor logs**:
   ```bash
   tail -f bot.log
   ```

## Customization

Edit `config.toml` to customize:
- File size limits
- Video duration limits
- Cache retention time
- Queue size and workers
- Log level and retention

Refer to `README.md` for detailed configuration options.
