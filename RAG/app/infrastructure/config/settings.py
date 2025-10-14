
# app/infrastructure/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL_PRE: str = "gpt-5-nano"
    OPENAI_MODEL_ANS: str = "gpt-5-nano"
    OPENAI_PROJECT_ID: str | None = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1" 

    # lee variables desde .env (en la raíz del proyecto RAG/)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# instancia única para inyectar
settings = Settings()
