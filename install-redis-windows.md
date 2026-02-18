# Redis Server Installation Guide (Windows - C: Drive)

## Option 1: Using MSI Installer (Recommended)

1. **Download Redis for Windows:**
   - Visit: https://github.com/microsoftarchive/redis/releases
   - Download: `Redis-x64-3.0.504.msi`

2. **Install to C: Drive:**
   - Run the MSI installer
   - Choose installation path: `C:\Redis`
   - Complete the installation wizard

3. **Add to System PATH:**
   - Open System Properties → Environment Variables
   - Edit System PATH variable
   - Add: `C:\Redis`
   - Click OK

4. **Verify Installation:**
   ```powershell
   redis-server --version
   ```

5. **Start Redis Server:**
   ```powershell
   redis-server
   ```

## Option 2: Using Chocolatey Package Manager

1. **Install Chocolatey** (if not installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install Redis:**
   ```powershell
   choco install redis-64 -y
   ```
   This installs to: `C:\ProgramData\chocolatey\lib\redis-64\tools`

3. **Start Redis as Windows Service:**
   ```powershell
   redis-server --service-install
   redis-server --service-start
   ```

## Option 3: Using Docker (Alternative)

If you have Docker installed:

```powershell
docker run -d -p 6379:6379 --name redis redis:latest
```

## Verify Redis is Running

```powershell
redis-cli ping
# Should return: PONG
```

## Configure Redis for Application

The application will connect to Redis at:
- Host: `localhost`
- Port: `6379`
- No password (default)

To change these settings, edit environment variables or `backend/app/config.py`.

## Troubleshooting

**Redis won't start:**
- Check if port 6379 is already in use
- Run as Administrator
- Check Windows Firewall settings

**Connection refused:**
- Ensure Redis server is running
- Check if localhost resolves correctly
- Verify port 6379 is not blocked
