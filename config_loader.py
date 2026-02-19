"""Configuration loader for the telegram bot."""
import tomllib
from pathlib import Path
from dataclasses import dataclass
from typing import List


@dataclass
class BotConfig:
    """Bot configuration."""
    token: str


@dataclass
class LimitsConfig:
    """Limits configuration."""
    max_file_size_mb: int
    max_video_duration_seconds: int


@dataclass
class CacheConfig:
    """Cache configuration."""
    retention_hours: int
    cache_dir: str


@dataclass
class QueueConfig:
    """Queue configuration."""
    max_size: int
    parallel_workers: int


@dataclass
class LoggingConfig:
    """Logging configuration."""
    log_file: str
    retention_days: int
    log_level: str


@dataclass
class WhitelistConfig:
    """Whitelist configuration."""
    user_ids: List[int]
    group_ids: List[int]


@dataclass
class Config:
    """Main configuration class."""
    bot: BotConfig
    limits: LimitsConfig
    cache: CacheConfig
    queue: QueueConfig
    logging: LoggingConfig
    whitelist: WhitelistConfig


def load_config(config_path: str = "config.toml") -> Config:
    """Load configuration from TOML file."""
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "rb") as f:
        data = tomllib.load(f)
    
    return Config(
        bot=BotConfig(**data["bot"]),
        limits=LimitsConfig(**data["limits"]),
        cache=CacheConfig(**data["cache"]),
        queue=QueueConfig(**data["queue"]),
        logging=LoggingConfig(**data["logging"]),
        whitelist=WhitelistConfig(**data["whitelist"])
    )
