from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")

    # API keys
    groq_api_key: Optional[str] = Field(default=None, alias="GROQ_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    huggingface_api_key: Optional[str] = Field(default=None, alias="HUGGINGFACE_API_KEY")
    horde_api_key: Optional[str] = Field(default=None, alias="HORDE_API_KEY")

    # DB
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Premium
    premium_price_stars: int = Field(default=100, alias="PREMIUM_PRICE_STARS")
    premium_days: int = Field(default=30, alias="PREMIUM_DAYS")
    free_daily_limit: int = Field(default=5, alias="FREE_DAILY_LIMIT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, int):
            return [v]
        return v or []

    @property
    def sqlalchemy_url(self) -> str:
        if self.database_url:
            return self.database_url
        return "sqlite+aiosqlite:///bot.db"


settings = Settings()