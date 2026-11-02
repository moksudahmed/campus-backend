from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OTP_EXPIRE_MINUTES: int = 5
    OTP_RESEND_SECONDS: int = 2
    OTP_MAX_ATTEMPTS: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
