# Production Deployment - Quick Reference

## What Changed

### Files Modified
1. **Dockerfile** - Production-ready multi-stage build with Gunicorn
2. **docker-compose.yml** - Proper production configuration with networking
3. **nginx.conf** - Production-grade reverse proxy configuration
4. **settings.py** - Added WhiteNoise, static file configuration
5. **requirements.txt** - Added gunicorn and whitenoise
6. **run_web.sh** - Enhanced startup script with migrations and static file collection

### Files Created
1. **gunicorn_config.py** - Gunicorn configuration for optimal performance
2. **PRODUCTION_DEPLOYMENT.md** - Comprehensive deployment guide

## Key Improvements

### 1. Application Server
- **Before**: Django development server (`runserver`)
- **After**: Gunicorn (production-grade WSGI server)
- **Benefit**: Handles concurrent requests efficiently

### 2. Static Files
- **Before**: Django serves them (slow)
- **After**: Nginx serves with caching headers + WhiteNoise fallback
- **Benefit**: Faster delivery, reduced server load

### 3. Networking
- **Before**: Django exposed on port 8123, no isolation
- **After**: Django internal only, Nginx proxies on port 80
- **Benefit**: Better security and proper separation of concerns

### 4. Docker Image
- **Before**: Full Python image (~800MB)
- **After**: Multi-stage build with slim image (~200MB)
- **Benefit**: Faster deployments, less storage

### 5. Container Health
- **Before**: No health checks
- **After**: Health checks for both Django and Nginx
- **Benefit**: Better monitoring and auto-recovery

## Quick Start

### 1. Build Images
```bash
docker-compose build
```

### 2. Start Services
```bash
docker-compose up -d
```

### 3. Verify Running
```bash
docker-compose ps
curl http://localhost
```

## Port Mapping

| Service | Port | Purpose |
|---------|------|---------|
| Nginx | 80 | HTTP requests from users |
| Nginx | 443 | HTTPS (when configured) |
| Django | 8000 | Internal only (via Nginx) |

## Environment Variables Required

```bash
# Django
DJANGO_SECRET_KEY=<strong-random-key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,your-domain.com

# Database (if using PostgreSQL)
DJANGO_DATABASE_ENGINE=postgresql
POSTGRES_DB=nogdb
POSTGRES_USER=noguser
POSTGRES_PASSWORD=<password>
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Push Notifications
PUSH_VAPID_PUBLIC_KEY=<key>
PUSH_VAPID_PRIVATE_KEY=<key>
PUSH_VAPID_EMAIL=admin@your-domain.com
```

## Common Commands

```bash
# View logs
docker-compose logs -f django
docker-compose logs -f nginx

# Run migrations
docker-compose exec django python manage.py migrate

# Create superuser
docker-compose exec django python manage.py createsuperuser

# Collect static files
docker-compose exec django python manage.py collectstatic --noinput

# Access Django shell
docker-compose exec django python manage.py shell

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Full rebuild
docker-compose down && docker-compose build && docker-compose up -d
```

## Performance Configuration

### Gunicorn Workers
- Automatically calculated: `(CPU cores * 2) + 1`
- On 4-core server: 9 workers
- Adjust in `gunicorn_config.py` if needed

### Nginx Rate Limiting
- General: 10 req/s (burst 20)
- API: 30 req/s (burst 50)
- Adjust in `nginx.conf` if needed

## Production Checklist

- [ ] Set `DJANGO_DEBUG=False` in .env
- [ ] Configure `DJANGO_ALLOWED_HOSTS`
- [ ] Use strong `DJANGO_SECRET_KEY`
- [ ] Setup HTTPS with SSL certificates
- [ ] Configure proper database (PostgreSQL)
- [ ] Setup database backups
- [ ] Configure error logging
- [ ] Test health checks
- [ ] Monitor resource usage
- [ ] Setup log rotation

## Troubleshooting

### Port already in use
```bash
# Kill process using port 80
sudo lsof -i :80
sudo kill -9 <PID>
```

### Static files not loading
```bash
# Collect static files
docker-compose exec django python manage.py collectstatic --noinput --clear

# Restart nginx
docker-compose restart nginx
```

### Migration errors
```bash
# Check database connection
docker-compose exec django python manage.py dbshell

# Run migrations manually
docker-compose exec django python manage.py migrate --verbose
```

## HTTPS Setup

### 1. Get SSL Certificate
```bash
# Using Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com
```

### 2. Update nginx.conf
- Uncomment HTTPS server block
- Update certificate paths
- Update server_name to your domain
- Uncomment HTTP redirect

### 3. Restart Nginx
```bash
docker-compose restart nginx
```

## Architecture Diagram

```
User Request
    ↓
Nginx (Port 80)
    ├─ /static/* → Serve from /app/staticfiles (cached)
    ├─ /media/* → Serve from /app/media
    ├─ /health/ → No rate limit
    ├─ /api/* → Rate limit 30 req/s
    ├─ /admin/* → Rate limit 10 req/s
    └─ /* → Rate limit 10 req/s
    ↓
Gunicorn (Port 8000 - Internal)
    ↓
Django Application
    ├─ Process requests
    ├─ Database queries
    └─ Business logic
    ↓
Database
```

## Files by Purpose

### Application
- `nog_app/Dockerfile` - Production Dockerfile
- `gunicorn_config.py` - Gunicorn worker configuration
- `requirements.txt` - Python dependencies

### Deployment
- `docker-compose.yml` - Container orchestration
- `nginx/Dockerfile` - Nginx image
- `nginx/nginx.conf` - Nginx configuration

### Django
- `nog_app/settings.py` - Django production settings
- `nog_app/run_web.sh` - Startup script
- `nog_app/wsgi.py` - WSGI application

## Resource Requirements

### Minimum (Small App)
- CPU: 1 core
- RAM: 512MB
- Disk: 5GB

### Recommended (Medium App)
- CPU: 2-4 cores
- RAM: 2-4GB
- Disk: 20GB

### High Traffic
- CPU: 8+ cores
- RAM: 8GB+
- Disk: 100GB+

## Next Steps

1. **Configure SSL** - Enable HTTPS
2. **Setup Database** - Use external PostgreSQL
3. **Enable Backups** - Automated backups
4. **Monitor** - Add monitoring/alerting
5. **CDN** - Setup CDN for static files
6. **DNS** - Point domain to server

---

See `PRODUCTION_DEPLOYMENT.md` for comprehensive guide.
