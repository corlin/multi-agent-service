"""Application settings and configuration."""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_debug: bool = Field(default=False, alias="API_DEBUG")
    
    # Model Service Configuration
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    qwen_api_key: Optional[str] = Field(default=None, alias="QWEN_API_KEY")
    deepseek_api_key: Optional[str] = Field(default=None, alias="DEEPSEEK_API_KEY")
    glm_api_key: Optional[str] = Field(default=None, alias="GLM_API_KEY")
    
    # Model Service URLs
    openai_api_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_URL")
    qwen_api_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", alias="QWEN_API_URL")
    deepseek_api_url: str = Field(default="https://api.deepseek.com/v1", alias="DEEPSEEK_API_URL")
    glm_api_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4", alias="GLM_API_URL")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./multi_agent_service.db", alias="DATABASE_URL")
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }


# Global settings instance
settings = Settings()