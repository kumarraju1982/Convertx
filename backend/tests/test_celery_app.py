"""
Unit tests for Celery application configuration.

Tests Celery app initialization, configuration settings, and Redis connection.
Validates Requirements 10.1.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from celery import Celery
from celery.schedules import crontab

from app.celery_app import create_celery_app
from app.config import Config, DevelopmentConfig, TestingConfig


class TestCeleryAppCreation:
    """Tests for Celery application creation."""
    
    def test_creates_celery_instance(self):
        """Test that create_celery_app returns a Celery instance."""
        app = create_celery_app()
        
        assert isinstance(app, Celery)
        assert app.main == 'pdf_converter'
    
    def test_uses_provided_config(self):
        """Test that create_celery_app uses provided configuration."""
        config = TestingConfig()
        config.CELERY_BROKER_URL = 'redis://testhost:6380/1'
        config.CELERY_RESULT_BACKEND = 'redis://testhost:6380/1'
        
        app = create_celery_app(config)
        
        assert app.conf.broker_url == 'redis://testhost:6380/1'
        assert app.conf.result_backend == 'redis://testhost:6380/1'
    
    def test_uses_default_config_when_none_provided(self):
        """Test that create_celery_app uses default config when none provided."""
        app = create_celery_app()
        
        # Should have broker and result backend configured
        assert app.conf.broker_url is not None
        assert app.conf.result_backend is not None
        assert 'redis://' in app.conf.broker_url


class TestCeleryConfiguration:
    """Tests for Celery configuration settings."""
    
    def test_broker_url_configuration(self):
        """Test that broker URL is correctly configured."""
        config = DevelopmentConfig()
        app = create_celery_app(config)
        
        assert app.conf.broker_url == config.CELERY_BROKER_URL
        assert 'redis://' in app.conf.broker_url
    
    def test_result_backend_configuration(self):
        """Test that result backend is correctly configured."""
        config = DevelopmentConfig()
        app = create_celery_app(config)
        
        assert app.conf.result_backend == config.CELERY_RESULT_BACKEND
        assert 'redis://' in app.conf.result_backend
    
    def test_task_serialization_settings(self):
        """Test that task serialization is configured correctly."""
        app = create_celery_app()
        
        assert app.conf.task_serializer == 'json'
        assert 'json' in app.conf.accept_content
        assert app.conf.result_serializer == 'json'
    
    def test_result_expiration_setting(self):
        """Test that result expiration is set to 24 hours."""
        app = create_celery_app()
        
        assert app.conf.result_expires == 86400  # 24 hours in seconds
    
    def test_task_execution_settings(self):
        """Test that task execution settings are configured."""
        app = create_celery_app()
        
        assert app.conf.task_track_started is True
        assert app.conf.task_time_limit == 3600  # 1 hour
        assert app.conf.task_soft_time_limit == 3300  # 55 minutes
    
    def test_broker_connection_settings(self):
        """Test that broker connection settings are configured."""
        app = create_celery_app()
        
        assert app.conf.broker_connection_retry_on_startup is True
        assert app.conf.broker_connection_retry is True
        assert app.conf.broker_connection_max_retries == 10
    
    def test_worker_settings(self):
        """Test that worker settings are configured."""
        app = create_celery_app()
        
        assert app.conf.worker_prefetch_multiplier == 1
        assert app.conf.worker_max_tasks_per_child == 1000
    
    def test_timezone_settings(self):
        """Test that timezone is set to UTC."""
        app = create_celery_app()
        
        assert app.conf.timezone == 'UTC'
        assert app.conf.enable_utc is True


class TestCeleryBeatSchedule:
    """Tests for Celery Beat periodic task schedule."""
    
    def test_cleanup_task_scheduled(self):
        """Test that cleanup task is scheduled in beat schedule."""
        app = create_celery_app()
        
        assert 'cleanup-old-files' in app.conf.beat_schedule
    
    def test_cleanup_task_configuration(self):
        """Test that cleanup task is configured correctly."""
        app = create_celery_app()
        
        cleanup_config = app.conf.beat_schedule['cleanup-old-files']
        
        assert cleanup_config['task'] == 'app.tasks.cleanup_old_files_task'
        assert cleanup_config['args'] == (24,)  # 24 hours
    
    def test_cleanup_task_schedule_is_hourly(self):
        """Test that cleanup task runs every hour."""
        app = create_celery_app()
        
        cleanup_config = app.conf.beat_schedule['cleanup-old-files']
        schedule = cleanup_config['schedule']
        
        assert isinstance(schedule, crontab)
        # Runs at minute 0 of every hour
        assert schedule.minute == {0}


class TestCeleryTaskDiscovery:
    """Tests for Celery task auto-discovery."""
    
    @patch.object(Celery, 'autodiscover_tasks')
    def test_autodiscovers_app_tasks(self, mock_autodiscover):
        """Test that Celery autodiscovers tasks from app module."""
        app = create_celery_app()
        
        # Verify autodiscover_tasks was called with 'app' module
        mock_autodiscover.assert_called_once_with(['app'])


class TestCeleryWithDifferentConfigs:
    """Tests for Celery with different configuration environments."""
    
    def test_development_config(self):
        """Test Celery with development configuration."""
        config = DevelopmentConfig()
        app = create_celery_app(config)
        
        assert app.conf.broker_url is not None
        assert 'localhost' in app.conf.broker_url or '127.0.0.1' in app.conf.broker_url
    
    def test_testing_config(self):
        """Test Celery with testing configuration."""
        config = TestingConfig()
        # Update Celery URLs to use testing DB
        config.CELERY_BROKER_URL = f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}'
        config.CELERY_RESULT_BACKEND = f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}'
        
        app = create_celery_app(config)
        
        # Testing config uses DB 1
        assert '/1' in app.conf.broker_url
        assert '/1' in app.conf.result_backend
    
    def test_custom_redis_host(self):
        """Test Celery with custom Redis host."""
        config = DevelopmentConfig()
        config.REDIS_HOST = 'custom-redis-host'
        config.CELERY_BROKER_URL = f'redis://{config.REDIS_HOST}:6379/0'
        config.CELERY_RESULT_BACKEND = f'redis://{config.REDIS_HOST}:6379/0'
        
        app = create_celery_app(config)
        
        assert 'custom-redis-host' in app.conf.broker_url
        assert 'custom-redis-host' in app.conf.result_backend
    
    def test_custom_redis_port(self):
        """Test Celery with custom Redis port."""
        config = DevelopmentConfig()
        config.REDIS_PORT = 6380
        config.CELERY_BROKER_URL = f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0'
        config.CELERY_RESULT_BACKEND = f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/0'
        
        app = create_celery_app(config)
        
        assert ':6380' in app.conf.broker_url
        assert ':6380' in app.conf.result_backend


class TestCeleryAppInstance:
    """Tests for the default Celery app instance."""
    
    def test_default_celery_app_exists(self):
        """Test that default celery_app instance is created."""
        from app.celery_app import celery_app
        
        assert celery_app is not None
        assert isinstance(celery_app, Celery)
    
    def test_default_celery_app_is_configured(self):
        """Test that default celery_app is properly configured."""
        from app.celery_app import celery_app
        
        assert celery_app.conf.broker_url is not None
        assert celery_app.conf.result_backend is not None
        assert celery_app.conf.task_serializer == 'json'


class TestCeleryConfigurationConsistency:
    """Tests for configuration consistency and validation."""
    
    def test_broker_and_backend_use_same_redis(self):
        """Test that broker and result backend use the same Redis instance."""
        config = DevelopmentConfig()
        app = create_celery_app(config)
        
        # Extract host and port from URLs
        broker_parts = app.conf.broker_url.split('/')
        backend_parts = app.conf.result_backend.split('/')
        
        # Should use same Redis server (host:port)
        assert broker_parts[2] == backend_parts[2]  # host:port part
    
    def test_time_limits_are_consistent(self):
        """Test that soft time limit is less than hard time limit."""
        app = create_celery_app()
        
        assert app.conf.task_soft_time_limit < app.conf.task_time_limit
    
    def test_result_expiration_matches_file_cleanup(self):
        """Test that result expiration aligns with file cleanup schedule."""
        app = create_celery_app()
        config = DevelopmentConfig()
        
        # Result expires in 24 hours
        assert app.conf.result_expires == 86400
        
        # File cleanup also runs with 24 hour threshold
        cleanup_config = app.conf.beat_schedule['cleanup-old-files']
        assert cleanup_config['args'] == (24,)
