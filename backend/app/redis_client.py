"""
Redis client module with connection pooling.

This module provides a Redis client with connection pooling for efficient
connection management and reuse across the application.
"""

import redis
from redis.connection import ConnectionPool
from typing import Optional
from app.config import Config


class RedisClient:
    """
    Redis client with connection pooling.
    
    This class manages a connection pool to Redis and provides methods
    for getting Redis connections. The connection pool is shared across
    the application to efficiently manage connections.
    """
    
    _pool: Optional[ConnectionPool] = None
    _client: Optional[redis.Redis] = None
    
    @classmethod
    def initialize(cls, config: Config) -> None:
        """
        Initialize the Redis connection pool.
        
        Args:
            config: Configuration object containing Redis settings
        """
        if cls._pool is not None:
            return  # Already initialized
        
        # Create connection pool with configuration
        cls._pool = ConnectionPool(
            host=config.REDIS_HOST,
            port=config.REDIS_PORT,
            db=config.REDIS_DB,
            password=config.REDIS_PASSWORD,
            max_connections=config.REDIS_MAX_CONNECTIONS,
            socket_timeout=config.REDIS_SOCKET_TIMEOUT,
            socket_connect_timeout=config.REDIS_SOCKET_CONNECT_TIMEOUT,
            socket_keepalive=config.REDIS_SOCKET_KEEPALIVE,
            retry_on_timeout=config.REDIS_RETRY_ON_TIMEOUT,
            decode_responses=True  # Automatically decode responses to strings
        )
        
        # Create Redis client using the pool
        cls._client = redis.Redis(connection_pool=cls._pool)
    
    @classmethod
    def get_client(cls) -> redis.Redis:
        """
        Get the Redis client instance.
        
        Returns:
            redis.Redis: Redis client instance
            
        Raises:
            RuntimeError: If Redis client is not initialized
        """
        if cls._client is None:
            raise RuntimeError(
                "Redis client not initialized. Call RedisClient.initialize() first."
            )
        return cls._client
    
    @classmethod
    def ping(cls) -> bool:
        """
        Test Redis connection.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            client = cls.get_client()
            return client.ping()
        except Exception:
            return False
    
    @classmethod
    def close(cls) -> None:
        """
        Close the Redis connection pool.
        
        This should be called when shutting down the application to
        properly clean up connections.
        """
        if cls._pool is not None:
            cls._pool.disconnect()
            cls._pool = None
            cls._client = None


def get_redis_client() -> redis.Redis:
    """
    Convenience function to get the Redis client.
    
    Returns:
        redis.Redis: Redis client instance
    """
    return RedisClient.get_client()
