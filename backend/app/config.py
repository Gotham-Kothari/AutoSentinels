from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AutoSentinels Backend"
    environment: str = Field("local", description="local | dev | prod")

    # LLM / Agent configs
    llm_provider: str = Field("anthropic", description="anthropic | openai | groq")
    llm_model: str = Field(
        "claude-3-5-sonnet-latest",
        description="Default LLM model",
    )

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    anthropic_api_key: str | None = None  # ⬅️ ADD THIS

    # Database configs
    sqlite_url: str = "sqlite+aiosqlite:///./autosentinels.db"

    use_firebase: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
