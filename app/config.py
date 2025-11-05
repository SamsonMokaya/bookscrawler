from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    APP_NAME: str = "Book Scraper API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Redis Settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Celery Settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    
    # MongoDB Settings
    MONGODB_USERNAME: str = "admin"
    MONGODB_PASSWORD: str = "admin123"
    MONGODB_DB_NAME: str = "bookscrawler"
    MONGODB_URL: str = "mongodb://admin:admin123@localhost:27017/bookscrawler?authSource=admin"
    
    # API Security Settings
    API_KEY_NAME: str = "X-API-Key"
    API_KEYS: str = "dev-key-001,dev-key-002,dev-key-003,admin-key-999"
    BLOCKED_API_KEYS: str = ""
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    @property
    def valid_api_keys(self) -> list:
        """Parse comma-separated API keys into list"""
        return [key.strip() for key in self.API_KEYS.split(',') if key.strip()]
    
    @property
    def blocked_api_keys(self) -> list:
        """Parse comma-separated blocked API keys into list"""
        if not self.BLOCKED_API_KEYS:
            return []
        return [key.strip() for key in self.BLOCKED_API_KEYS.split(',') if key.strip()]
    
    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour in seconds
    
    # Crawler Settings
    TARGET_URL: str = "https://books.toscrape.com"
    CRAWLER_DELAY: float = 0.5
    CRAWLER_MAX_RETRIES: int = 3
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_CONCURRENT_REQUESTS: int = 10
    
    # Scheduler Settings
    ENABLE_SCHEDULER: bool = True
    CRAWL_SCHEDULE_HOUR: int = 2
    CRAWL_SCHEDULE_MINUTE: int = 0
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Email Alerts (Optional)
    ENABLE_EMAIL_ALERTS: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = "your-email@gmail.com"
    SMTP_PASSWORD: str = "your-app-password"
    ALERT_EMAIL: str = "admin@example.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

