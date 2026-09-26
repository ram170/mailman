from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    shopify_webhook_secret: str

    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    review_email: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()