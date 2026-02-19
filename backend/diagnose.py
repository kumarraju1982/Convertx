"""
Diagnostic script to check PDF to Word converter setup.

Run this to identify configuration issues.
"""

import sys
import os

def check_redis():
    """Check if Redis is accessible."""
    print("Checking Redis connection...")
    try:
        from app.redis_client import RedisClient
        from app.config import get_config
        
        redis_client = RedisClient()
        redis_client.initialize(get_config())
        conn = redis_client.get_client()
        
        # Try to ping Redis
        conn.ping()
        print("✓ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Make sure Redis is running: redis-server")
        return False

def check_celery():
    """Check if Celery can be imported and configured."""
    print("\nChecking Celery configuration...")
    try:
        from app.celery_app import celery_app
        print(f"✓ Celery app created: {celery_app.main}")
        print(f"  Broker: {celery_app.conf.broker_url}")
        return True
    except Exception as e:
        print(f"✗ Celery configuration failed: {e}")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed."""
    print("\nChecking Tesseract OCR...")
    try:
        import pytesseract
        from PIL import Image
        
        # Try to get Tesseract version
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract is installed: version {version}")
        return True
    except Exception as e:
        print(f"✗ Tesseract not found: {e}")
        print("  Install Tesseract OCR:")
        print("  - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        print("  - macOS: brew install tesseract")
        print("  - Linux: sudo apt-get install tesseract-ocr")
        return False

def check_upload_folder():
    """Check if upload folder exists and is writable."""
    print("\nChecking upload folder...")
    try:
        from app.config import get_config
        config = get_config()
        upload_folder = config.UPLOAD_FOLDER
        
        # Check if folder exists
        if not os.path.exists(upload_folder):
            print(f"  Creating upload folder: {upload_folder}")
            os.makedirs(upload_folder, exist_ok=True)
        
        # Check if writable
        test_file = os.path.join(upload_folder, '.test')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        
        print(f"✓ Upload folder is accessible: {upload_folder}")
        return True
    except Exception as e:
        print(f"✗ Upload folder check failed: {e}")
        return False

def check_dependencies():
    """Check if all required Python packages are installed."""
    print("\nChecking Python dependencies...")
    required = [
        'flask',
        'celery',
        'redis',
        'fitz',  # PyMuPDF
        'pytesseract',
        'docx',  # python-docx
        'PIL',  # Pillow
        'pdf2docx'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    return True

def check_celery_worker():
    """Check if Celery worker is running."""
    print("\nChecking Celery worker status...")
    try:
        from app.celery_app import celery_app
        
        # Inspect active workers
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            print(f"✓ Celery worker(s) running: {list(active_workers.keys())}")
            return True
        else:
            print("✗ No Celery workers detected")
            print("  Start a worker with: celery -A app.celery_app worker --loglevel=info")
            return False
    except Exception as e:
        print(f"✗ Could not check worker status: {e}")
        print("  Make sure Redis is running first")
        return False

def main():
    """Run all diagnostic checks."""
    print("=" * 60)
    print("PDF to Word Converter - Diagnostic Tool")
    print("=" * 60)
    
    checks = [
        check_dependencies,
        check_redis,
        check_celery,
        check_upload_folder,
        check_tesseract,
        check_celery_worker
    ]
    
    results = []
    for check in checks:
        try:
            results.append(check())
        except Exception as e:
            print(f"\nUnexpected error in {check.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Checks passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All checks passed! Your setup looks good.")
        print("\nTo start the application:")
        print("1. Start Redis: redis-server")
        print("2. Start Celery worker: celery -A app.celery_app worker --loglevel=info")
        print("3. Start Flask: flask run")
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
