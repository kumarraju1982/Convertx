# Redis Configuration

This module provides Redis connection management with connection pooling for the PDF to Word Converter application.

## Features

- **Connection Pooling**: Efficient connection reuse with configurable pool size
- **Environment-based Configuration**: Easy configuration via environment variables
- **Multiple Environments**: Support for development, production, and testing configurations
- **Automatic Reconnection**: Retry on timeout for resilient connections
- **Socket Keep-Alive**: Maintains persistent connections

## Configuration

### Environment Variables

Configure Redis connection using the following environment variables:

```bash
# Redis Server
REDIS_HOST=localhost          # Default: localhost
REDIS_PORT=6379              # Default: 6379
REDIS_DB=0                   # Default: 0
REDIS_PASSWORD=              # Default: None (no password)

# Connection Pool Settings
REDIS_MAX_CONNECTIONS=50     # Default: 50
REDIS_SOCKET_TIMEOUT=5       # Default: 5 seconds
REDIS_SOCKET_CONNECT_TIMEOUT=5  # Default: 5 seconds
REDIS_SOCKET_KEEPALIVE=true  # Default: true
REDIS_RETRY_ON_TIMEOUT=true  # Default: true

# Application Environment
FLASK_ENV=development        # Options: development, production, testing
```

### Configuration Classes

The application provides three configuration classes:

- **DevelopmentConfig**: For local development (default)
- **ProductionConfig**: For production deployment
- **TestingConfig**: For running tests (uses Redis DB 1)

## Usage

### Initialize Redis Client

```python
from app.config import get_config
from app.redis_client import RedisClient

# Get configuration for current environment
config = get_config()

# Initialize Redis client with connection pool
RedisClient.initialize(config)
```

### Get Redis Client

```python
from app.redis_client import get_redis_client

# Get the Redis client instance
redis_client = get_redis_client()

# Use Redis operations
redis_client.set('key', 'value')
value = redis_client.get('key')
```

### Test Connection

```python
from app.redis_client import RedisClient

# Test if Redis is reachable
if RedisClient.ping():
    print("Redis connection successful")
else:
    print("Redis connection failed")
```

### Cleanup

```python
from app.redis_client import RedisClient

# Close connection pool when shutting down
RedisClient.close()
```

## Connection Pool Benefits

The connection pool provides several advantages:

1. **Performance**: Reuses existing connections instead of creating new ones
2. **Resource Management**: Limits the number of concurrent connections
3. **Reliability**: Automatically handles connection failures and retries
4. **Efficiency**: Reduces overhead of connection establishment

## Local Development Setup

1. **Install Redis** (if not already installed):
   - Windows: Download from https://redis.io/download or use WSL
   - macOS: `brew install redis`
   - Linux: `sudo apt-get install redis-server`

2. **Start Redis Server**:
   ```bash
   redis-server
   ```

3. **Verify Redis is Running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

4. **Run the Application**:
   ```bash
   # The application will automatically connect to Redis on localhost:6379
   python app.py
   ```

## Production Deployment

For production, consider:

1. **Use Redis Password**: Set `REDIS_PASSWORD` environment variable
2. **Adjust Pool Size**: Increase `REDIS_MAX_CONNECTIONS` based on load
3. **Use Redis Sentinel or Cluster**: For high availability
4. **Enable Persistence**: Configure Redis RDB or AOF persistence
5. **Monitor Connections**: Use Redis INFO command to monitor pool usage

## Testing

The Redis configuration includes comprehensive unit tests:

```bash
# Run Redis client tests
pytest tests/test_redis_client.py -v

# Run with coverage
pytest tests/test_redis_client.py --cov=app.redis_client --cov=app.config
```

## Troubleshooting

### Connection Refused

If you see "Connection refused" errors:
- Ensure Redis server is running: `redis-cli ping`
- Check Redis is listening on correct port: `redis-cli -p 6379 ping`
- Verify firewall settings allow connections to Redis port

### Authentication Failed

If you see "NOAUTH Authentication required":
- Set `REDIS_PASSWORD` environment variable
- Or configure Redis to not require password (for development only)

### Too Many Connections

If you see "max number of clients reached":
- Increase Redis `maxclients` configuration
- Reduce `REDIS_MAX_CONNECTIONS` in application config
- Check for connection leaks in application code

## Related Components

- **Celery**: Uses Redis as message broker and result backend
- **Job Manager**: Stores job state and progress in Redis
- **Session Storage**: Can use Redis for session management (future enhancement)
