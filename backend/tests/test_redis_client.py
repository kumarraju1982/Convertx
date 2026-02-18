"""
Unit tests for Redis client configuration and connection pooling.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.redis_client import RedisClient, get_redis_client
from app.config import Config, TestingConfig


class TestRedisClient:
    """Test suite for RedisClient class."""
    
    def setup_method(self):
        """Reset RedisClient state before each test."""
        RedisClient._pool = None
        RedisClient._client = None
    
    def teardown_method(self):
        """Clean up after each test."""
        if RedisClient._pool is not None:
            RedisClient.close()
    
    def test_initialize_creates_connection_pool(self):
        """Test that initialize creates a connection pool with correct settings."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool') as mock_pool_class, \
             patch('app.redis_client.redis.Redis') as mock_redis_class:
            
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            mock_client = Mock()
            mock_redis_class.return_value = mock_client
            
            RedisClient.initialize(config)
            
            # Verify ConnectionPool was created with correct parameters
            mock_pool_class.assert_called_once_with(
                host=config.REDIS_HOST,
                port=config.REDIS_PORT,
                db=config.REDIS_DB,
                password=config.REDIS_PASSWORD,
                max_connections=config.REDIS_MAX_CONNECTIONS,
                socket_timeout=config.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=config.REDIS_SOCKET_CONNECT_TIMEOUT,
                socket_keepalive=config.REDIS_SOCKET_KEEPALIVE,
                retry_on_timeout=config.REDIS_RETRY_ON_TIMEOUT,
                decode_responses=True
            )
            
            # Verify Redis client was created with the pool
            mock_redis_class.assert_called_once_with(connection_pool=mock_pool)
            
            assert RedisClient._pool is mock_pool
            assert RedisClient._client is mock_client
    
    def test_initialize_is_idempotent(self):
        """Test that calling initialize multiple times doesn't recreate the pool."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool') as mock_pool_class, \
             patch('app.redis_client.redis.Redis'):
            
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            
            RedisClient.initialize(config)
            first_pool = RedisClient._pool
            
            # Call initialize again
            RedisClient.initialize(config)
            second_pool = RedisClient._pool
            
            # Should be the same pool instance
            assert first_pool is second_pool
            # ConnectionPool should only be called once
            assert mock_pool_class.call_count == 1
    
    def test_get_client_returns_client(self):
        """Test that get_client returns the Redis client."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool'), \
             patch('app.redis_client.redis.Redis') as mock_redis_class:
            
            mock_client = Mock()
            mock_redis_class.return_value = mock_client
            
            RedisClient.initialize(config)
            client = RedisClient.get_client()
            
            assert client is mock_client
    
    def test_get_client_raises_if_not_initialized(self):
        """Test that get_client raises RuntimeError if not initialized."""
        with pytest.raises(RuntimeError, match="Redis client not initialized"):
            RedisClient.get_client()
    
    def test_ping_returns_true_on_success(self):
        """Test that ping returns True when connection is successful."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool'), \
             patch('app.redis_client.redis.Redis') as mock_redis_class:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            mock_redis_class.return_value = mock_client
            
            RedisClient.initialize(config)
            result = RedisClient.ping()
            
            assert result is True
            mock_client.ping.assert_called_once()
    
    def test_ping_returns_false_on_failure(self):
        """Test that ping returns False when connection fails."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool'), \
             patch('app.redis_client.redis.Redis') as mock_redis_class:
            
            mock_client = Mock()
            mock_client.ping.side_effect = Exception("Connection failed")
            mock_redis_class.return_value = mock_client
            
            RedisClient.initialize(config)
            result = RedisClient.ping()
            
            assert result is False
    
    def test_close_disconnects_pool(self):
        """Test that close properly disconnects the connection pool."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool') as mock_pool_class, \
             patch('app.redis_client.redis.Redis'):
            
            mock_pool = Mock()
            mock_pool_class.return_value = mock_pool
            
            RedisClient.initialize(config)
            RedisClient.close()
            
            mock_pool.disconnect.assert_called_once()
            assert RedisClient._pool is None
            assert RedisClient._client is None
    
    def test_get_redis_client_convenience_function(self):
        """Test the convenience function get_redis_client."""
        config = TestingConfig()
        
        with patch('app.redis_client.ConnectionPool'), \
             patch('app.redis_client.redis.Redis') as mock_redis_class:
            
            mock_client = Mock()
            mock_redis_class.return_value = mock_client
            
            RedisClient.initialize(config)
            client = get_redis_client()
            
            assert client is mock_client


class TestConfig:
    """Test suite for Config class."""
    
    def test_get_redis_url_without_password(self):
        """Test Redis URL generation without password."""
        config = Config()
        config.REDIS_HOST = 'localhost'
        config.REDIS_PORT = 6379
        config.REDIS_DB = 0
        config.REDIS_PASSWORD = None
        
        url = config.get_redis_url()
        assert url == 'redis://localhost:6379/0'
    
    def test_get_redis_url_with_password(self):
        """Test Redis URL generation with password."""
        # Create a custom config class with password
        class ConfigWithPassword(Config):
            REDIS_HOST = 'localhost'
            REDIS_PORT = 6379
            REDIS_DB = 0
            REDIS_PASSWORD = 'secret123'
        
        config = ConfigWithPassword()
        url = config.get_redis_url()
        assert url == 'redis://:secret123@localhost:6379/0'
    
    def test_default_configuration_values(self):
        """Test that default configuration values are set correctly."""
        config = Config()
        
        assert config.REDIS_HOST == 'localhost'
        assert config.REDIS_PORT == 6379
        assert config.REDIS_DB == 0
        assert config.REDIS_PASSWORD is None
        assert config.REDIS_MAX_CONNECTIONS == 50
        assert config.REDIS_SOCKET_TIMEOUT == 5
        assert config.REDIS_SOCKET_CONNECT_TIMEOUT == 5
        assert config.REDIS_SOCKET_KEEPALIVE is True
        assert config.REDIS_RETRY_ON_TIMEOUT is True
    
    def test_testing_config_uses_different_db(self):
        """Test that TestingConfig uses a different Redis DB."""
        config = TestingConfig()
        
        assert config.REDIS_DB == 1
        assert config.TESTING is True


class TestRedisClientWithCelery:
    """Tests for Redis client integration with Celery."""
    
    def test_redis_client_uses_same_config_as_celery(self):
        """Test that Redis client and Celery use consistent configuration."""
        from app.celery_app import create_celery_app
        from app.config import DevelopmentConfig
        
        config = DevelopmentConfig()
        app = create_celery_app(config)
        
        # Both should use same Redis host and port
        assert config.REDIS_HOST in app.conf.broker_url
        assert str(config.REDIS_PORT) in app.conf.broker_url
    
    def test_redis_connection_pool_settings(self, redis_client_class, mock_config):
        """Test that connection pool is configured with correct settings."""
        redis_client_class.initialize(mock_config)
        
        pool = redis_client_class._pool
        
        assert pool is not None
        assert pool.connection_kwargs['host'] == mock_config.REDIS_HOST
        assert pool.connection_kwargs['port'] == mock_config.REDIS_PORT
        assert pool.connection_kwargs['db'] == mock_config.REDIS_DB
        assert pool.max_connections == mock_config.REDIS_MAX_CONNECTIONS
