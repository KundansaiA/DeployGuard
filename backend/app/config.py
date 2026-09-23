"""Application settings loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_url: str = "postgresql://deployguard:deployguard@localhost:5432/deployguard"
    secret_key: str = "change-me"
    log_level: str = "INFO"

    # CORS — comma-separated list of allowed origins.
    # Local dev default allows the Vite dev server.
    # In production, set this to your exact frontend URL (no trailing slash).
    # Example: CORS_ORIGINS=https://deployguard.yourdomain.com
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # IBM watsonx.ai configuration
    # Leave api_key and project_id empty to disable AI explanations entirely.
    watsonx_api_key: str = ""
    watsonx_project_id: str = ""
    watsonx_url: str = "https://us-south.ml.cloud.ibm.com"
    watsonx_model_id: str = "ibm/granite-3-3-8b-instruct"
    watsonx_timeout_secs: int = 30

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS_ORIGINS as a Python list, stripping whitespace."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
