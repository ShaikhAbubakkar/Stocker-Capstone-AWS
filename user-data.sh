#!/bin/bash
set -e

# Stocker V2 - EC2 User Data Script
# This script runs automatically when EC2 instance launches
# Paste entire contents into AWS EC2 "User data" field during instance creation

# Update system packages
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y python3 python3-pip python3-venv git nginx supervisor curl wget

# Create application user
useradd -m -s /bin/bash stocker || true

# Clone repository (update URL if needed)
cd /home/stocker
sudo -u stocker git clone https://github.com/YOUR_USERNAME/Stocker-V2.git stocker-app
cd /home/stocker/stocker-app

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file from .env.example
cp .env.example .env
# Note: Update .env with actual values before starting (AWS_REGION, DynamoDB tables, SNS topic, etc.)

# Create directories for logs and socket files
mkdir -p /var/log/stocker
mkdir -p /run/stocker
chown -R stocker:stocker /var/log/stocker /run/stocker /home/stocker/stocker-app

# Setup Gunicorn with Supervisor
cat > /etc/supervisor/conf.d/stocker-gunicorn.conf << 'EOF'
[program:stocker-gunicorn]
directory=/home/stocker/stocker-app
command=/home/stocker/stocker-app/venv/bin/gunicorn --config gunicorn_config.py app:app
user=stocker
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/stocker/gunicorn.log
environment=PATH="/home/stocker/stocker-app/venv/bin",PYTHONUNBUFFERED=1
EOF

# Setup Nginx as reverse proxy
rm -f /etc/nginx/sites-enabled/default
cat > /etc/nginx/sites-available/stocker << 'EOF'
upstream gunicorn {
    server unix:/run/stocker/stocker.sock fail_timeout=0;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 10M;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Enable gzip compression
    gzip on;
    gzip_types text/plain text/css text/javascript application/json application/javascript;
    gzip_min_length 1024;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    limit_req zone=general burst=20 nodelay;

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/stocker/stocker-app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

ln -sf /etc/nginx/sites-available/stocker /etc/nginx/sites-enabled/stocker

# Test and start Nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

# Start Supervisor and Gunicorn
systemctl restart supervisor
systemctl enable supervisor

# Create healthcheck script
cat > /usr/local/bin/stocker-healthcheck << 'EOF'
#!/bin/bash
curl -f http://localhost/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    exit 0
else
    exit 1
fi
EOF
chmod +x /usr/local/bin/stocker-healthcheck

# Final configuration reminders
cat > /root/STOCKER_SETUP_NOTES.txt << 'EOF'
Stocker V2 EC2 Setup Complete!

NEXT STEPS:
1. SSH into instance and update /home/stocker/stocker-app/.env with:
   - AWS_REGION (e.g., us-east-1)
   - DynamoDB table names (UsersTable, PortfoliosTable, etc.)
   - SNS topic ARN for notifications
   - Flask secret key (generate: python3 -c "import secrets; print(secrets.token_hex(32))")

2. Initialize DynamoDB tables (run inside app directory):
   python3 << 'INIT'
   import boto3
   dynamodb = boto3.resource('dynamodb')
   # Create tables as defined in DATA_ARCHITECTURE.md
   INIT

3. Verify deployment:
   curl http://instance-ip
   sudo supervisorctl status stocker-gunicorn
   sudo tail -f /var/log/stocker/gunicorn.log

4. For HTTPS/SSL:
   - Install certbot: apt-get install -y certbot python3-certbot-nginx
   - Get certificate: certbot certonly --nginx -d your-domain.com
   - Update nginx config with SSL directives
   - Update DynamoDB IAM role to allow table operations
   - Ensure EC2 instance has IAM role with DynamoDB and SNS permissions

IMPORTANT:
- EC2 instance must have IAM role with permissions for:
  - DynamoDB: dynamodb:GetItem, dynamodb:PutItem, dynamodb:UpdateItem, dynamodb:Query
  - SNS: sns:Publish
- Do NOT commit .env file to git (add to .gitignore)
- Application logs: /var/log/stocker/gunicorn.log
- Supervisor logs: supervisorctl tail stocker-gunicorn
EOF

echo "✓ Stocker V2 EC2 setup complete!"
echo "✓ See /root/STOCKER_SETUP_NOTES.txt for next steps"
