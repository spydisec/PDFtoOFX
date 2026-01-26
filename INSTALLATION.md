# Installation Guide

Complete installation instructions for self-hosting ANZ Plus to OFX Converter on Linux.

## Prerequisites

- **Python 3.11+** installed on your system
- **Git** for cloning the repository
- Basic command-line knowledge

To verify your Python version:
```bash
python3 --version
```

## Linux Installation (Self-Hosting)

### 1. Clone the Repository

```bash
git clone https://github.com/spydisec/PDFtoOFX.git
cd PDFtoOFX
```

### 2. Create Virtual Environment

It's strongly recommended to use a virtual environment to isolate dependencies:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate
```

**Note:** Your terminal prompt should now show `(.venv)` indicating the virtual environment is active.

### 3. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI (web framework)
- Uvicorn (ASGI server)
- pdfplumber (PDF extraction)
- ofxtools (OFX generation)
- And other dependencies

### 4. Verify Installation

Run the test suite to ensure everything is working:

```bash
pytest tests/ -v
```

You should see all 6 tests passing:
```
✓ test_sequential_fitids_no_collision
✓ test_reference_number_priority  
✓ test_different_dates_independent_counters
✓ test_parse_transaction_line
✓ test_all_transactions_preserved
✓ test_full_conversion_produces_valid_ofx
```

## Usage

### Option 1: Web Interface (Recommended)

Start the web server:

```bash
python run_web.py
```

The application will be available at:
- **Main Interface:** http://localhost:8000
- **API Documentation:** http://localhost:8000/api/docs

**Features:**
- Drag-and-drop PDF upload
- Real-time conversion
- One-click OFX download
- Mobile-responsive design

**To stop the server:** Press `Ctrl+C`

### Option 2: Command Line Interface

For batch processing or automation:

```bash
python convert_pdf.py path/to/statement.pdf output.ofx
```

**Example:**
```bash
python convert_pdf.py statement.pdf my_transactions.ofx
```

## Production Deployment (Linux)

### Using systemd Service

Create a systemd service file for automatic startup and management.

#### 1. Create Service File

```bash
sudo nano /etc/systemd/system/pdftoofx.service
```

Add the following content:

```ini
[Unit]
Description=ANZ Plus to OFX Converter Web Service
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/path/to/PDFtoOFX
Environment="PATH=/path/to/PDFtoOFX/.venv/bin"
ExecStart=/path/to/PDFtoOFX/.venv/bin/python run_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Replace:**
- `YOUR_USERNAME` with your Linux username
- `/path/to/PDFtoOFX` with the actual installation path

#### 2. Enable and Start Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable pdftoofx.service

# Start the service immediately
sudo systemctl start pdftoofx.service

# Check service status
sudo systemctl status pdftoofx.service
```

#### 3. Service Management Commands

```bash
# View logs
sudo journalctl -u pdftoofx.service -f

# Restart service
sudo systemctl restart pdftoofx.service

# Stop service
sudo systemctl stop pdftoofx.service

# Disable auto-start
sudo systemctl disable pdftoofx.service
```

### Using Nginx Reverse Proxy (Optional)

For production deployments, use Nginx as a reverse proxy:

#### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

#### 2. Configure Nginx

Create a new site configuration:

```bash
sudo nano /etc/nginx/sites-available/pdftoofx
```

Add the following:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or server IP

    client_max_body_size 10M;  # Allow PDF uploads up to 10MB

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Enable Site and Restart Nginx

```bash
# Create symbolic link to enable site
sudo ln -s /etc/nginx/sites-available/pdftoofx /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

#### 4. SSL/HTTPS with Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

### Using Docker (Alternative)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run_web.py"]
```

Build and run:

```bash
# Build Docker image
docker build -t pdftoofx .

# Run container
docker run -d \
  --name pdftoofx \
  -p 8000:8000 \
  --restart unless-stopped \
  pdftoofx

# View logs
docker logs -f pdftoofx

# Stop container
docker stop pdftoofx
```

## Updating the Application

To update to the latest version:

```bash
# Navigate to project directory
cd PDFtoOFX

# Activate virtual environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests to verify
pytest tests/ -v

# Restart the service (if using systemd)
sudo systemctl restart pdftoofx.service
```

## Troubleshooting

### Virtual Environment Issues

**Problem:** `source .venv/bin/activate` not working

**Solution:** Ensure you're in the project directory and the virtual environment was created successfully:
```bash
# Recreate virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Port Already in Use

**Problem:** Port 8000 is already in use

**Solution:** Find and stop the process using port 8000:
```bash
# Find process using port 8000
sudo lsof -i :8000

# Stop the process (replace PID with actual process ID)
sudo kill -9 PID
```

Or modify `run_web.py` to use a different port:
```python
uvicorn.run(app, host="0.0.0.0", port=8080)  # Changed from 8000 to 8080
```

### Permission Denied Errors

**Problem:** Permission errors when running as service

**Solution:** Ensure the service user has read/write permissions:
```bash
# Change ownership to service user
sudo chown -R YOUR_USERNAME:YOUR_USERNAME /path/to/PDFtoOFX

# Set proper permissions
chmod -R 755 /path/to/PDFtoOFX
```

### Dependency Installation Fails

**Problem:** pip install fails with compilation errors

**Solution:** Install development headers:
```bash
# For Ubuntu/Debian
sudo apt-get install python3-dev build-essential

# For RHEL/CentOS/Fedora
sudo yum install python3-devel gcc
```

### Web Interface Not Accessible

**Problem:** Can't access http://localhost:8000

**Solution:** Check if the service is running:
```bash
# If using systemd
sudo systemctl status pdftoofx.service

# If running manually, check process
ps aux | grep python | grep run_web
```

Also verify firewall settings:
```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 8000/tcp

# RHEL/CentOS (firewalld)
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

## Security Considerations

### For Production Deployments

1. **Run behind Nginx/Apache:** Don't expose the Python application directly to the internet
2. **Use HTTPS:** Always use SSL/TLS certificates (Let's Encrypt is free)
3. **Restrict file uploads:** The application already limits PDFs to 10MB
4. **Regular updates:** Keep Python, dependencies, and the application up to date
5. **Firewall rules:** Only allow necessary ports (80/443 for HTTP/HTTPS)
6. **User permissions:** Run the service as a non-privileged user
7. **Monitor logs:** Regularly check application and system logs

### File Security

The application is designed with security in mind:
- Files are processed in memory when possible
- Temporary files are automatically deleted after download
- No data persistence or database storage
- Stateless architecture prevents data leaks

## Deactivating Virtual Environment

When you're done working with the application:

```bash
deactivate
```

This returns you to your system's default Python environment.

## Additional Resources

- **Project Repository:** https://github.com/spydisec/PDFtoOFX
- **Issue Tracker:** https://github.com/spydisec/PDFtoOFX/issues
- **Architecture Documentation:** See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Main Documentation:** See [README.md](README.md)

## Support

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/spydisec/PDFtoOFX/issues)
2. Review the [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
3. Create a new issue with detailed error messages and system information
