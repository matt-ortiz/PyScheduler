#!/bin/bash
set -e

echo "Starting Tempo..."

# Create necessary directories
mkdir -p /data/scripts /data/logs /data/backups
mkdir -p /var/log/nginx /var/lib/nginx
mkdir -p /var/log/supervisor

# Set proper permissions
chown -R www-data:www-data /data
chmod -R 755 /data

# Initialize database
echo "Initializing database..."
cd /app
export PYTHONPATH="/app"
python -c "from backend.database import init_database; init_database()"

# Redis will be started by supervisor - no need to start it here

# Remove nginx default site
rm -f /etc/nginx/sites-enabled/default

# Enable our nginx config
ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# Test nginx configuration
nginx -t

echo "Starting services with supervisor..."
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/tempo.conf