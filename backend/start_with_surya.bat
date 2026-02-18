@echo off
REM Start Celery worker with Surya OCR
set OCR_ENGINE=surya
celery -A app.celery_app worker --loglevel=info --pool=solo
