"""
Configuration module for the PDF to Word Converter application.

This module provides configuration settings for Redis, Celery, and other
application components.
"""

import os
from typing import Optional


class Config:
    """Base configuration class."""
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_PASSWORD: Optional[str] = os.getenv('REDIS_PASSWORD', None)
    
    # Redis Connection Pool Settings
    REDIS_MAX_CONNECTIONS: int = int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
    REDIS_SOCKET_KEEPALIVE: bool = os.getenv('REDIS_SOCKET_KEEPALIVE', 'true').lower() == 'true'
    REDIS_RETRY_ON_TIMEOUT: bool = os.getenv('REDIS_RETRY_ON_TIMEOUT', 'true').lower() == 'true'
    
    # Celery Configuration
    @classmethod
    def get_celery_broker_url(cls) -> str:
        """Get Celery broker URL with password support."""
        return cls.get_redis_url()
    
    @classmethod
    def get_celery_result_backend(cls) -> str:
        """Get Celery result backend URL with password support."""
        return cls.get_redis_url()
    
    CELERY_BROKER_URL: str = property(lambda self: self.get_celery_broker_url())
    CELERY_RESULT_BACKEND: str = property(lambda self: self.get_celery_result_backend())
    
    # File Storage Configuration
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'uploads')))
    MAX_FILE_SIZE: int = int(os.getenv('MAX_FILE_SIZE', str(50 * 1024 * 1024)))  # 50MB default
    FILE_CLEANUP_AGE_HOURS: int = int(os.getenv('FILE_CLEANUP_AGE_HOURS', '24'))
    
    # OCR Engine Configuration
    # Options: 'tesseract' (fast, lower accuracy) or 'surya' (slower, higher accuracy)
    OCR_ENGINE: str = os.getenv('OCR_ENGINE', 'tesseract').lower()
    
    @classmethod
    def validate_ocr_engine(cls) -> str:
        """
        Validate and return the OCR engine setting.
        
        Returns:
            str: Valid OCR engine name ('tesseract' or 'surya')
            
        Raises:
            ValueError: If OCR_ENGINE is not valid
        """
        valid_engines = ['tesseract', 'surya']
        if cls.OCR_ENGINE not in valid_engines:
            raise ValueError(
                f"Invalid OCR_ENGINE '{cls.OCR_ENGINE}'. "
                f"Must be one of: {', '.join(valid_engines)}"
            )
        return cls.OCR_ENGINE
    
    @classmethod
    def get_redis_url(cls) -> str:
        """
        Get the Redis connection URL.
        
        Returns:
            str: Redis connection URL with optional password
        """
        if cls.REDIS_PASSWORD:
            return f'redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}'
        return f'redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}'


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""
    DEBUG = True
    TESTING = True
    REDIS_DB = 1  # Use different DB for testing


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: Optional[str] = None) -> Config:
    """
    Get configuration object based on environment.
    
    Args:
        env: Environment name ('development', 'production', 'testing')
        
    Returns:
        Config: Configuration object for the specified environment
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
