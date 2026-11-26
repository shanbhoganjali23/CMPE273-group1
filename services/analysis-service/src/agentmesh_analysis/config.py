from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ANALYSIS_", extra="ignore")

    port: int = Field(default=8001, ge=1, le=65535)
    bind_host: str = "127.0.0.1"
