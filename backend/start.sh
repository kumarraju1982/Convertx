#!/bin/bash
# Startup script for Render deployment

# Start gunicorn with proper configuration
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --timeout 300 --worker-class sync --log-level info "app.api:create_app()"
