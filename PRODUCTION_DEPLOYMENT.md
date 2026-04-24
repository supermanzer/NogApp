# Production Deployment Guide for NogApp

This guide explains how to deploy your Django NogApp with Gunicorn and Nginx in production using Docker.

## Overview

Your application now uses:
- **Gunicorn**: High-performance Python WSGI HTTP Server
- **Nginx**: Reverse proxy and static file server
- **WhiteNoise**: Efficient static file serving
- **Docker**: Containerized deployment

## Architecture

```
User Request
    ↓
Nginx (Port 80/443)
    ├─ Serves static files directly (/static/, /media/)
    ├─ Rate limits requests
    └─ Proxies dynamic requests to Gunicorn
    ↓
Gunicorn (Port 8000)
    └─ Runs Django application
    ↓
Django Application
    └─ Processes requests
```

## Prerequisites

- Docker and Docker Compose installed
- `.env` file configured with:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG=False`
  - `DJANGO_ALLOWED_HOSTS` (comma-separated list)
  - Database credentials (if using PostgreSQL)

## Building & Running

### 1. Build the Images

```bash
docker-compose build
```

This will:
- Build the Django/Gunicorn image using multi-stage build
- Build the Nginx image
- Install all dependencies

### 2. Start the Services

```bash
docker-compose up -d
```

This will:
- Start the Django container
- Run migrations automatically
- Collect static files
- Start Gunicorn with optimal worker configuration
- Start Nginx on port 80

### 3. Verify Everything is Running

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f django    # Django/Gunicorn logs
docker-compose logs -f nginx     # Nginx logs

# Test the application
curl http://localhost
```

## Key Changes Made

### 1. **Dockerfile** - Production Optimizations
- Multi-stage build to reduce image size
- Uses `python:3.13-slim` instead of full image
- Installs only runtime dependencies
- Creates non-root user for security
- Uses Gunicorn instead of Django dev server

### 2. **docker-compose.yml** - Proper Configuration
- Removed direct port exposure for Django (only internal access)
- Added named volumes for static files
- Health checks for both services
- Service dependency management
- Environment variables for production
- Shared network for container communication

### 3. **nginx.conf** - Production Configuration
- Proper upstream configuration
- Static file serving with caching
- Rate limiting per endpoint
- Security headers
- Error handling
- Gzip compression ready
- HTTPS configuration template

### 4. **gunicorn_config.py** - Worker Configuration
- Optimal worker count: `(CPU * 2) + 1`
- Proper timeouts
- Logging configuration
- Server hooks for lifecycle management

### 5. **settings.py** - Production Settings
- WhiteNoise middleware for static files
- Proper static file configuration
- STATIC_ROOT for collected files

### 6. **requirements.txt** - Added Dependencies
- `gunicorn==21.2.0` - Application server
- `whitenoise==6.6.0` - Static file serving

## Configuration Details

### Environment Variables

Required in `.env`:

```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DJANGO_DATABASE_ENGINE=postgresql
DJANGO_DATABASE_NAME=nogdb
DJANGO_DATABASE_USER=noguser
DJANGO_DATABASE_PASSWORD=your-password
DJANGO_DATABASE_HOST=postgres
DJANGO_DATABASE_PORT=5432

# Push Notifications
PUSH_VAPID_PUBLIC_KEY=your-public-key
PUSH_VAPID_PRIVATE_KEY=your-private-key
PUSH_VAPID_EMAIL=admin@your-domain.com
```

### Gunicorn Workers

The number of workers is automatically calculated:
- **Formula**: `(CPU cores * 2) + 1`
- **Example**: On a 4-core server: `(4 * 2) + 1 = 9 workers`
- **Modifiable**: Edit `gunicorn_config.py` if needed

### Nginx Rate Limiting

```
- General endpoints: 10 req/s with burst of 20
- API endpoints: 30 req/s with burst of 50
- Health checks: No rate limiting
```

## Performance Tuning

### Increase Worker Count

Edit `gunicorn_config.py`:

```python
workers = 16  # Set explicitly instead of auto-calculation
```

Then rebuild:
```bash
docker-compose build django
docker-compose up -d django
```

### Adjust Timeouts

In `gunicorn_config.py`:
```python
timeout = 60  # Increase for long-running operations
```

### Enable Caching

In `nginx.conf`, static files are cached for 30 days:
```
expires 30d;
add_header Cache-Control "public, immutable";
```

## Database Setup (PostgreSQL)

If using PostgreSQL (recommended for production):

### Option 1: Docker Database

Add to `docker-compose.yml`:

```yaml
postgres:
  image: postgres:15-alpine
  container_name: nog_postgres
  volumes:
    - postgres_data:/var/lib/postgresql/data
  environment:
    POSTGRES_DB: nogdb
    POSTGRES_USER: noguser
    POSTGRES_PASSWORD: ${DB_PASSWORD}
  networks:
    - nog_network
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U noguser"]
    interval: 10s
    timeout: 5s
    retries: 5

volumes:
  postgres_data:
```

### Option 2: External PostgreSQL

Update `.env` with your PostgreSQL credentials and set `DJANGO_DATABASE_HOST`.

## Monitoring & Logging

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f django
docker-compose logs -f nginx

# Follow specific number of lines
docker-compose logs -f --tail 50 django
```

### Health Checks

Both services have health checks configured:

```bash
# Check Django health
curl -f http://localhost:8000/

# Check Nginx health
curl -f http://localhost/health/
```

### Log Locations (in containers)

- Django/Gunicorn: `/app/logs/` (mounted from host)
- Nginx: `/var/log/nginx/` (mounted from host at `./logs/nginx/`)

## SSL/HTTPS Setup

### Option 1: Let's Encrypt with Certbot

```bash
# Install certbot
pip install certbot certbot-nginx

# Get certificates
sudo certbot certonly --standalone -d your-domain.com

# Certificate location: /etc/letsencrypt/live/your-domain.com/
```

### Option 2: Self-Signed Certificate (Testing Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/key.pem \
  -out /etc/nginx/ssl/cert.pem
```

### Update nginx.conf

Uncomment the HTTPS server block in `nginx.conf` and:
1. Update certificate paths
2. Update `server_name` to your domain
3. Uncomment the HTTP redirect

## Static Files Management

### Collect Static Files

```bash
# Automatic on startup, but can be done manually:
docker-compose exec django python manage.py collectstatic --noinput
```

### Static Files Location

- In container: `/app/staticfiles/`
- On host: `./staticfiles/`
- Served by Nginx with caching headers

## Database Migrations

Migrations run automatically on startup. To run manually:

```bash
docker-compose exec django python manage.py migrate
```

## Maintenance Commands

### Backup Database

```bash
# PostgreSQL in Docker
docker-compose exec postgres pg_dump -U noguser nogdb > backup.sql

# Restore
docker-compose exec -T postgres psql -U noguser nogdb < backup.sql
```

### Clean Old Files

```bash
# Remove old static files
docker-compose exec django python manage.py clean_old_files

# Clear cache
docker-compose exec django python manage.py clear_cache
```

### Create Superuser

```bash
docker-compose exec django python manage.py createsuperuser
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs django
docker-compose logs nginx

# Check if ports are in use
lsof -i :80
lsof -i :8000
```

### Static files not loading

```bash
# Collect again
docker-compose exec django python manage.py collectstatic --noinput --clear

# Restart nginx
docker-compose restart nginx
```

### Database connection error

```bash
# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec django python manage.py dbshell
```

### Permission issues

```bash
# Fix ownership
docker-compose exec django chown -R appuser:appuser /app
```

## Production Checklist

- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure `DJANGO_ALLOWED_HOSTS`
- [ ] Use a strong `DJANGO_SECRET_KEY`
- [ ] Setup HTTPS/SSL certificates
- [ ] Configure proper database (PostgreSQL recommended)
- [ ] Setup database backups
- [ ] Configure error logging/monitoring
- [ ] Setup log rotation
- [ ] Configure proper health checks
- [ ] Test failover scenarios
- [ ] Setup monitoring and alerting
- [ ] Configure CDN for static files (optional)
- [ ] Setup CORS if needed
- [ ] Enable GZIP compression
- [ ] Configure security headers

## Performance Tips

1. **Enable caching** on static files
2. **Use a CDN** for static assets
3. **Optimize images** before serving
4. **Enable database query caching** with Redis
5. **Increase Gunicorn workers** on high-traffic servers
6. **Monitor CPU and memory** usage
7. **Use connection pooling** for database
8. **Enable compression** on Nginx

## Rollback Procedure

```bash
# If deployment has issues:

# Stop current version
docker-compose down

# Revert code to previous version
git checkout <previous-tag>

# Rebuild images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Next Steps

1. **Update DNS** to point to your server
2. **Setup HTTPS** with SSL certificates
3. **Configure email** for password resets
4. **Setup monitoring** (New Relic, DataDog, etc.)
5. **Setup backups** for database and static files
6. **Configure CDN** for static assets

## Additional Resources

- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [WhiteNoise Documentation](https://whitenoise.readthedocs.io/)
