# Celery Application Configuration

This document describes the Celery application setup for the PDF to Word Converter.

## Overview

The Celery application is configured to use Redis as both the message broker and result backend. This enables asynchronous task processing for PDF conversion jobs.

## Configuration

The Celery app is configured with the following settings:

### Broker and Result Backend
- **Broker URL**: Redis connection for task queue
- **Result Backend**: Redis connection for storing task results

### Task Serialization
- **Task Serializer**: JSON
- **Accept Content**: JSON only
- **Result Serializer**: JSON

### Result Expiration
- **Result Expires**: 24 hours (86400 seconds)
- Results are automatically cleaned up after 24 hours

### Task Execution
- **Track Started**: Enabled (allows tracking when tasks start)
- **Time Limit**: 1 hour (3600 seconds) hard limit
- **Soft Time Limit**: 55 minutes (3300 seconds) soft limit

### Connection Settings
- **Retry on Startup**: Enabled
- **Connection Retry**: Enabled
- **Max Retries**: 10 attempts

### Worker Settings
- **Prefetch Multiplier**: 1 (workers fetch one task at a time)
- **Max Tasks Per Child**: 1000 (worker restarts after 1000 tasks)

## Usage

### Importing the Celery App

```python
from app.celery_app import celery_app
```

### Creating a Task

```python
from app.celery_app import celery_app

@celery_app.task(bind=True)
def my_task(self, arg1, arg2):
    # Task implementation
    return result
```

### Running a Celery Worker

```bash
# Development
celery -A app.celery_app worker --loglevel=info

# Production (with concurrency)
celery -A app.celery_app worker --loglevel=info --concurrency=4
```

### Monitoring with Flower (Optional)

```bash
celery -A app.celery_app flower
```

Then visit http://localhost:5555 to see the Flower dashboard.

## Environment Variables

The Celery configuration uses the following environment variables (via `app.config`):

- `REDIS_HOST`: Redis server host (default: localhost)
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_DB`: Redis database number (default: 0)
- `REDIS_PASSWORD`: Redis password (optional)
- `CELERY_BROKER_URL`: Override broker URL (optional)
- `CELERY_RESULT_BACKEND`: Override result backend URL (optional)

## Testing

The Celery app can be tested by importing it:

```python
from app.celery_app import celery_app

# Check configuration
print(celery_app.conf.broker_url)
print(celery_app.conf.result_backend)
```

## Requirements Satisfied

This implementation satisfies **Requirement 10.1**: "WHEN a conversion job is created, THE Job_Queue SHALL add it to the processing queue"

The Celery application provides the infrastructure for:
- Queueing conversion jobs
- Processing jobs asynchronously
- Tracking job status and progress
- Storing task results
