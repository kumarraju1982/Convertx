#!/usr/bin/env python
"""Quick script to check coverage of individual modules."""

import subprocess
import sys

modules_to_test = [
    ("file_manager", "tests/test_file_manager.py"),
    ("job_manager", "tests/test_job_manager.py"),
    ("document_parser", "tests/test_document_parser.py"),
    ("layout_analyzer", "tests/test_layout_analyzer.py"),
    ("ocr_engine", "tests/test_ocr_engine.py"),
    ("word_generator", "tests/test_word_generator.py"),
    ("pdf_converter", "tests/test_pdf_converter.py"),
    ("redis_client", "tests/test_redis_client.py"),
    ("api", "tests/test_api.py"),
    ("tasks", "tests/test_tasks.py"),
]

print("Module Coverage Report")
print("=" * 60)

for module_name, test_file in modules_to_test:
    cmd = [
        sys.executable, "-m", "pytest", test_file,
        f"--cov=app.{module_name}",
        "--cov-report=term-missing",
        "--no-cov-on-fail",
        "-q"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Extract coverage percentage
    for line in result.stdout.split('\n'):
        if f'app\\{module_name}.py' in line or f'app/{module_name}.py' in line:
            parts = line.split()
            if len(parts) >= 4:
                coverage = parts[3]
                print(f"{module_name:20s}: {coverage}")
                break
    else:
        print(f"{module_name:20s}: ERROR or NO COVERAGE")

print("=" * 60)
