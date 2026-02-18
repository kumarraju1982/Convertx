# Tesseract OCR Installation Guide (Windows - C: Drive)

## Installation Steps

1. **Download Tesseract OCR:**
   - Visit: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest installer: `tesseract-ocr-w64-setup-5.3.3.20231005.exe`

2. **Install to C: Drive:**
   - Run the installer
   - Choose installation path: `C:\Program Files\Tesseract-OCR`
   - **IMPORTANT:** Check "Add to PATH" during installation
   - Select language data: At minimum, install "English"
   - Complete the installation

3. **Verify Installation:**
   ```powershell
   tesseract --version
   ```
   Should display version information.

4. **Add to System PATH (if not done during install):**
   - Open System Properties → Environment Variables
   - Edit System PATH variable
   - Add: `C:\Program Files\Tesseract-OCR`
   - Click OK
   - Restart terminal

5. **Set TESSDATA_PREFIX Environment Variable:**
   ```powershell
   [Environment]::SetEnvironmentVariable("TESSDATA_PREFIX", "C:\Program Files\Tesseract-OCR\tessdata", "Machine")
   ```

## Verify Tesseract Works with Python

```powershell
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

If you get an error about tesseract not found, set the path in Python:

```python
# In your Python code or config
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Language Data

Tesseract needs language data files for OCR. The installer includes English by default.

**Location:** `C:\Program Files\Tesseract-OCR\tessdata\`

**To add more languages:**
1. Download language files from: https://github.com/tesseract-ocr/tessdata
2. Copy `.traineddata` files to: `C:\Program Files\Tesseract-OCR\tessdata\`

## Test OCR Functionality

Create a test image with text and run:

```powershell
tesseract test_image.png output
```

This should create `output.txt` with the recognized text.

## Troubleshooting

**"tesseract is not recognized":**
- Verify PATH includes `C:\Program Files\Tesseract-OCR`
- Restart terminal/PowerShell
- Restart computer if needed

**Python can't find tesseract:**
- Set `pytesseract.pytesseract.tesseract_cmd` explicitly
- Or add to backend config:
  ```python
  # backend/app/config.py
  TESSERACT_CMD = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```

**Poor OCR accuracy:**
- Ensure image quality is good (300+ DPI)
- Use preprocessing (grayscale, contrast adjustment)
- Install additional language data if needed

## Integration with Application

The application uses `pytesseract` which is already installed. It will automatically find Tesseract if it's in PATH.

If needed, configure the path in `backend/app/config.py`:

```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```
