from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TaxFlow AI"
    default_currency: str = "INR"

    # Prefer DATABASE_URL from environment; keep optional so the app can still boot
    # for non-DB commands (e.g., static checks) without failing settings load.
    database_url: str = ""

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60

    cors_origins: str = "http://localhost:5173"

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = ""


settings = Settings()

