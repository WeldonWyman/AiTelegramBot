"""Main Telegram bot implementation."""
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from pathlib import Path
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command

from config_loader import load_config
from cache_manager import CacheManager
from downloader import MediaDownloader
from queue_manager import DownloadQueue, DownloadTask


class MediaBot:
    """Telegram bot for downloading media."""
    
    def __init__(self, config_path: str = "config.toml"):
        """Initialize bot.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Setup logging
        self._setup_logging()
        
        # Initialize components
        self.cache_manager = CacheManager(
            self.config.cache.cache_dir,
            self.config.cache.retention_hours
        )
        
        self.downloader = MediaDownloader(
            self.config.cache.cache_dir,
            self.config.limits.max_file_size_mb,
            self.config.limits.max_video_duration_seconds
        )
        
        self.queue = DownloadQueue(
            self.config.queue.max_size,
            self.config.queue.parallel_workers
        )
        
        # Initialize bot and dispatcher
        self.bot = Bot(token=self.config.bot.token)
        self.dp = Dispatcher()
        
        # Register handlers
        self._register_handlers()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Bot initialized successfully")
    
    def _setup_logging(self):
        """Setup logging with rotation."""
        # Create logs directory if needed
        log_path = Path(self.config.logging.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logger = logging.getLogger()
        logger.setLevel(getattr(logging, self.config.logging.log_level))
        
        # Remove existing handlers
        logger.handlers = []
        
        # Create rotating file handler
        # maxBytes = 10MB, keep logs for retention_days
        file_handler = RotatingFileHandler(
            self.config.logging.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=self.config.logging.retention_days
        )
        file_handler.setLevel(getattr(logging, self.config.logging.log_level))
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    def _register_handlers(self):
        """Register message handlers."""
        self.dp.message.register(self._cmd_start, Command("start"))
        self.dp.message.register(self._cmd_help, Command("help"))
        self.dp.message.register(self._cmd_status, Command("status"))
        self.dp.message.register(self._handle_url, F.text)
    
    def _is_user_allowed(self, user_id: int, chat_id: int) -> bool:
        """Check if user is in whitelist.
        
        Args:
            user_id: User ID
            chat_id: Chat ID
            
        Returns:
            True if user is allowed
        """
        # If whitelists are empty, allow all users
        if not self.config.whitelist.user_ids and not self.config.whitelist.group_ids:
            return True
        
        # Check user whitelist
        if self.config.whitelist.user_ids and user_id in self.config.whitelist.user_ids:
            return True
        
        # Check group whitelist (for group chats)
        if self.config.whitelist.group_ids and chat_id in self.config.whitelist.group_ids:
            return True
        
        return False
    
    async def _cmd_start(self, message: Message):
        """Handle /start command."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        self.logger.info(f"User {user_id} sent /start command")
        
        if not self._is_user_allowed(user_id, chat_id):
            await message.reply("Sorry, you are not authorized to use this bot.")
            self.logger.warning(f"Unauthorized user {user_id} attempted to use bot")
            return
        
        welcome_text = (
            "👋 Welcome to Media Downloader Bot!\n\n"
            "I can download media from various platforms and send them to you.\n\n"
            "Just send me a URL and I'll download it for you.\n\n"
            "Use /help to see available commands."
        )
        await message.reply(welcome_text)
    
    async def _cmd_help(self, message: Message):
        """Handle /help command."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not self._is_user_allowed(user_id, chat_id):
            await message.reply("Sorry, you are not authorized to use this bot.")
            return
        
        help_text = (
            "📖 Available commands:\n\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Show queue status\n\n"
            "To download media, simply send me a URL.\n\n"
            f"⚠️ Limits:\n"
            f"• Max file size: {self.config.limits.max_file_size_mb}MB\n"
            f"• Max video duration: {self.config.limits.max_video_duration_seconds}s\n"
            f"• Queue size: {self.config.queue.max_size}\n"
        )
        await message.reply(help_text)
    
    async def _cmd_status(self, message: Message):
        """Handle /status command."""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not self._is_user_allowed(user_id, chat_id):
            await message.reply("Sorry, you are not authorized to use this bot.")
            return
        
        queue_size = self.queue.get_queue_size()
        active_count = self.queue.get_active_count()
        
        status_text = (
            f"📊 Queue Status:\n\n"
            f"• Tasks in queue: {queue_size}/{self.config.queue.max_size}\n"
            f"• Active downloads: {active_count}/{self.config.queue.parallel_workers}\n"
        )
        await message.reply(status_text)
    
    async def _handle_url(self, message: Message):
        """Handle URL messages."""
        if not message.text:
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Check if user is allowed
        if not self._is_user_allowed(user_id, chat_id):
            await message.reply("Sorry, you are not authorized to use this bot.")
            self.logger.warning(f"Unauthorized user {user_id} attempted to download: {message.text}")
            return
        
        # Check if message looks like a URL
        text = message.text.strip()
        if not (text.startswith('http://') or text.startswith('https://')):
            return
        
        self.logger.info(f"User {user_id} requested download: {text}")
        
        # Check if already in cache
        cached_file = self.cache_manager.get_cached_file(text)
        if cached_file:
            self.logger.info(f"Serving from cache: {text}")
            await message.reply("📂 Found in cache! Sending...")
            
            try:
                # Send cached file
                video = FSInputFile(cached_file)
                await message.reply_video(video)
                self.logger.info(f"Successfully sent cached file to user {user_id}: {text}")
                return
            except Exception as e:
                self.logger.error(f"Error sending cached file: {e}", exc_info=True)
                await message.reply(f"❌ Error sending cached file: {str(e)}")
                return
        
        # Check if queue is full
        if self.queue.is_full():
            await message.reply(
                f"⏳ Queue is full ({self.config.queue.max_size} tasks). Please try again later."
            )
            self.logger.warning(f"Queue full, rejected request from user {user_id}")
            return
        
        # Add to queue
        task = DownloadTask(
            url=text,
            user_id=user_id,
            chat_id=chat_id,
            message_id=message.message_id,
            timestamp=datetime.now()
        )
        
        if await self.queue.add_task(task):
            queue_position = self.queue.get_queue_size()
            await message.reply(
                f"✅ Added to queue (position: {queue_position})\n"
                f"Please wait while I download your media..."
            )
        else:
            await message.reply("❌ Failed to add to queue. Please try again.")
            self.logger.error(f"Failed to add task to queue for user {user_id}")
    
    async def _process_download(self, task: DownloadTask):
        """Process a download task.
        
        Args:
            task: Download task to process
        """
        self.logger.info(f"Processing download for user {task.user_id}: {task.url}")
        
        try:
            # Download the file
            file_path, error_msg, file_info = await self.downloader.download(task.url)
            
            if error_msg:
                # Download failed
                await self.bot.send_message(
                    task.chat_id,
                    f"❌ Download failed: {error_msg}",
                    reply_to_message_id=task.message_id
                )
                self.logger.error(f"Download failed for user {task.user_id}: {task.url} - {error_msg}")
                return
            
            if not file_path or not os.path.exists(file_path):
                await self.bot.send_message(
                    task.chat_id,
                    "❌ Download failed: File not found",
                    reply_to_message_id=task.message_id
                )
                self.logger.error(f"Download file not found for user {task.user_id}: {task.url}")
                return
            
            # Add to cache
            self.cache_manager.add_to_cache(task.url, file_path, file_info)
            
            # Send the file
            self.logger.info(f"Sending file to user {task.user_id}: {file_path}")
            
            try:
                video = FSInputFile(file_path)
                caption = f"📹 {file_info.get('title', 'Video')}"
                
                await self.bot.send_video(
                    task.chat_id,
                    video,
                    caption=caption,
                    reply_to_message_id=task.message_id
                )
                
                self.logger.info(f"Successfully sent file to user {task.user_id}: {task.url}")
                
            except Exception as e:
                await self.bot.send_message(
                    task.chat_id,
                    f"❌ Error sending file: {str(e)}",
                    reply_to_message_id=task.message_id
                )
                self.logger.error(f"Error sending file to user {task.user_id}: {e}", exc_info=True)
                
        except Exception as e:
            self.logger.error(f"Unexpected error processing download: {e}", exc_info=True)
            try:
                await self.bot.send_message(
                    task.chat_id,
                    f"❌ Unexpected error: {str(e)}",
                    reply_to_message_id=task.message_id
                )
            except Exception:
                pass
    
    async def _cleanup_cache_periodically(self):
        """Periodically clean up expired cache entries."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                self.logger.info("Running cache cleanup")
                await self.cache_manager.cleanup_expired()
            except Exception as e:
                self.logger.error(f"Error during cache cleanup: {e}", exc_info=True)
    
    async def start(self):
        """Start the bot."""
        self.logger.info("Starting bot...")
        
        # Start queue workers
        await self.queue.start_workers(self._process_download)
        
        # Start cache cleanup task
        asyncio.create_task(self._cleanup_cache_periodically())
        
        # Start polling
        self.logger.info("Bot is running...")
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the bot."""
        self.logger.info("Stopping bot...")
        
        # Stop queue workers
        await self.queue.stop_workers()
        
        # Close bot session
        await self.bot.session.close()
        
        self.logger.info("Bot stopped")


async def main():
    """Main entry point."""
    # Check if config file exists
    if not os.path.exists("config.toml"):
        print("Error: config.toml not found!")
        print("Please copy config.example.toml to config.toml and configure it.")
        sys.exit(1)
    
    # Create and start bot
    bot = MediaBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
