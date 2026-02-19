#!/bin/bash
# Build script for Render.com deployment
# Installs system dependencies and Python packages

echo "Installing system dependencies..."
apt-get update
apt-get install -y tesseract-ocr tesseract-ocr-eng

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Build complete!"
