from pydantic_settings import BaseSettings
from pydantic import AnyUrl, Field
from typing import Optional


class Settings(BaseSettings):
    # Twilio configuration
    twilio_account_sid: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    twilio_from_number: str = Field(..., alias="TWILIO_FROM_NUMBER")

    # Owner/command authority
    owner_phone: str = Field(..., alias="OWNER_PHONE")

    # Instagram thread to monitor
    ig_thread_url: AnyUrl = Field(..., alias="IG_THREAD_URL")

    # Polling interval (seconds)
    poll_seconds: int = Field(90, alias="POLL_SECONDS")

    # Optional app secret for admin endpoints
    app_secret_token: Optional[str] = Field(None, alias="APP_SECRET_TOKEN")

    # Paths for persistent data (mounted volume on Render)
    data_dir: str = Field("/data", alias="DATA_DIR")
    user_data_dir_name: str = Field("user_data_dir", alias="USER_DATA_DIR_NAME")
    state_db_name: str = Field("state.db", alias="STATE_DB_NAME")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


