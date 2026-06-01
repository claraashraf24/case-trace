from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "CaseTrace AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str = "casetrace_user"
    POSTGRES_PASSWORD: str = "casetrace_password"
    POSTGRES_DB: str = "casetrace_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4.1-mini"
    USE_LLM_EXTRACTION: bool = True
    USE_LLM_ASSISTANT: bool = True

    DATABASE_URL: str = (
        "postgresql+psycopg://casetrace_user:casetrace_password"
        "@localhost:5432/casetrace_db"
    )
    USE_LLM_HYPOTHESES: bool = True

    class Config:
        env_file = ".env"


settings = Settings()