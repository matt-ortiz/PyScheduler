FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    redis-server \
    supervisor \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/dist/ ./frontend/
COPY VERSION ./VERSION

# Copy configuration files
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/tempo.conf
COPY docker/start.sh /start.sh
COPY docker/start-simple.sh /start-simple.sh
COPY docker/redis.conf /etc/redis/redis.conf

# Make start scripts executable
RUN chmod +x /start.sh /start-simple.sh

# Create data directory and set permissions
RUN mkdir -p /data/scripts /data/logs /data/backups && \
    chown -R www-data:www-data /data && \
    chmod -R 755 /data

# Create nginx directories
RUN mkdir -p /var/log/nginx /var/lib/nginx

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start supervisor
CMD ["/start.sh"]