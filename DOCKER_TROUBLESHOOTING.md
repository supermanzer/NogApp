# Docker Production Deployment Troubleshooting Guide

## General Debugging

### 1. Check Container Status
```bash
# See running containers
docker-compose ps

# See all containers (including stopped)
docker-compose ps -a

# See detailed container info
docker-compose ps -v
```

### 2. View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs django
docker-compose logs nginx

# Follow logs in real-time
docker-compose logs -f django

# Last 50 lines
docker-compose logs --tail 50 django

# Timestamps included
docker-compose logs -f --timestamps django

# Specific time range
docker-compose logs --since 10m --until 5m
```

### 3. Check Resource Usage
```bash
# CPU, memory, network I/O
docker stats

# Specific container
docker stats nog_django

# No streaming (single output)
docker stats --no-stream
```

---

## Common Issues & Solutions

### Issue 1: "Port already in use"

**Symptoms:**
```
Error response from daemon: driver failed programming external connectivity on endpoint: 
Bind for 0.0.0.0:80 failed: port is already allocated
```

**Solutions:**

```bash
# Find what's using port 80
lsof -i :80
netstat -tlnp | grep :80

# Kill the process (Linux/Mac)
sudo kill -9 <PID>

# Or use different port in docker-compose.yml
ports:
  - "8080:80"  # Use 8080 instead of 80
```

---

### Issue 2: Containers won't start

**Symptoms:**
```
docker-compose up -d
ERROR: for nog_django Cannot start service django: OCI runtime create failed
```

**Solutions:**

```bash
# Check logs for the error
docker-compose logs django

# Common causes:
# 1. Insufficient disk space
df -h

# 2. Docker daemon not running
sudo systemctl start docker

# 3. Corrupted container
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d

# 4. Permission issues
sudo usermod -aG docker $USER
```

---

### Issue 3: Static files not loading (404 errors)

**Symptoms:**
- Images, CSS, JS returning 404
- `/static/*` requests fail
- Works in development but not in production

**Solutions:**

```bash
# Collect static files again
docker-compose exec django python manage.py collectstatic --noinput --clear

# Verify static files exist
docker-compose exec django ls -la staticfiles/

# Check permissions
docker-compose exec django ls -lad staticfiles/

# Restart nginx to serve new files
docker-compose restart nginx

# Verify nginx can read files
docker-compose exec nginx ls -la /app/staticfiles/

# Check nginx config
docker-compose exec nginx nginx -t  # Test config
```

---

### Issue 4: Database connection errors

**Symptoms:**
```
django.db.utils.OperationalError: could not connect to server
psycopg2.OperationalError: could not connect to server
```

**Solutions:**

```bash
# Check if postgres is running (if using Docker)
docker-compose ps postgres

# Test connection
docker-compose exec django python manage.py dbshell

# Check environment variables in .env
cat .env | grep DATABASE

# Check database logs
docker-compose logs postgres

# Verify host and port
docker-compose exec django python -c "
import os
print('DB Engine:', os.environ.get('DJANGO_DATABASE_ENGINE'))
print('DB Name:', os.environ.get('POSTGRES_DB'))
print('DB User:', os.environ.get('POSTGRES_USER'))
print('DB Host:', os.environ.get('POSTGRES_HOST'))
print('DB Port:', os.environ.get('POSTGRES_PORT'))
"

# If using external database, verify connectivity
docker-compose exec django apt-get update && apt-get install -y netcat
docker-compose exec django nc -zv your-database-host 5432
```

---

### Issue 5: Gunicorn not starting

**Symptoms:**
```
django exited with code 1
```

**Solutions:**

```bash
# Check logs for error
docker-compose logs django

# Common errors:
# 1. Import error - check requirements.txt
# 2. Settings error - check DJANGO_SETTINGS_MODULE
# 3. Syntax error - check gunicorn_config.py

# Test locally in container
docker-compose exec django python manage.py check

# Test gunicorn config
docker-compose exec django gunicorn --check-config gunicorn_config.py

# Run with verbose output
docker-compose exec django gunicorn \
  --config /app/gunicorn_config.py \
  --workers=1 \
  --timeout=60 \
  --log-level=debug \
  nog_app.wsgi:application
```

---

### Issue 6: Nginx returning 502 Bad Gateway

**Symptoms:**
```
502 Bad Gateway
502 Service Temporarily Unavailable
```

**Solutions:**

```bash
# Check if Django is running
docker-compose ps django

# Check Django health
curl http://localhost:8000/  # (from inside nginx container)
docker-compose exec nginx curl http://django:8000/

# Check nginx logs
docker-compose logs nginx

# Test nginx config
docker-compose exec nginx nginx -t

# Check upstream configuration
docker-compose exec nginx cat /etc/nginx/conf.d/default.conf

# Verify DNS resolution inside container
docker-compose exec nginx nslookup django

# Restart both services
docker-compose restart django nginx

# Check if connection is being refused
docker-compose exec django netstat -tlnp | grep 8000
```

---

### Issue 7: Out of memory (OOM)

**Symptoms:**
```
Killed (container stopped)
Cannot allocate memory
```

**Solutions:**

```bash
# Check memory usage
docker stats --no-stream

# Check system memory
free -h
df -h

# Reduce Gunicorn workers
# Edit gunicorn_config.py
workers = 3  # Instead of (CPU * 2) + 1

# Rebuild and restart
docker-compose build django
docker-compose up -d django

# Set memory limit in docker-compose.yml
services:
  django:
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

# Restart
docker-compose up -d
```

---

### Issue 8: High CPU usage

**Symptoms:**
```
docker stats shows 100% CPU
Server very slow
```

**Solutions:**

```bash
# Check which container
docker stats

# Check Django processes
docker-compose exec django ps aux

# Check for infinite loops
docker-compose logs --tail 100 django | grep -i error

# Increase workers (if under 80% CPU utilization)
# Edit gunicorn_config.py
workers = 12  # Increase from auto

# Check for slow queries
docker-compose exec django python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import CaptureQueriesContext
>>> # Profile slow queries

# Restart with reduced load
docker-compose restart
```

---

### Issue 9: Permission denied errors

**Symptoms:**
```
Permission denied: '/app/staticfiles'
Cannot write to log file
```

**Solutions:**

```bash
# Check file ownership
docker-compose exec django ls -la /app/staticfiles/

# Fix ownership (inside container)
docker-compose exec django chown -R appuser:appuser /app

# Fix log directory
docker-compose exec django mkdir -p /app/logs
docker-compose exec django chown -R appuser:appuser /app/logs

# Restart
docker-compose restart django

# Verify on host (if volume mounted)
ls -la ./nog_app/staticfiles/
sudo chown -R $USER:$USER ./nog_app/staticfiles/
```

---

### Issue 10: Migrations failing

**Symptoms:**
```
django.db.utils.OperationalError: no such table
psycopg2.errors.UndefinedTable: relation "X" does not exist
```

**Solutions:**

```bash
# Run migrations manually
docker-compose exec django python manage.py migrate --verbose

# Check migration status
docker-compose exec django python manage.py showmigrations

# Check for missing migrations
docker-compose exec django python manage.py makemigrations --check

# Reset database (for development only!)
docker-compose exec django python manage.py flush --noinput
docker-compose exec django python manage.py migrate

# Specific app migration
docker-compose exec django python manage.py migrate nogoff

# View SQL for migration
docker-compose exec django python manage.py sqlmigrate nogoff 0001

# Rollback migration
docker-compose exec django python manage.py migrate nogoff 0001
```

---

## Network Issues

### Can't reach service from another container

```bash
# Test connectivity
docker-compose exec nginx ping django

# Check DNS
docker-compose exec nginx nslookup django

# Check network
docker network ls
docker network inspect <network_name>

# Ensure both containers on same network
docker-compose exec django hostname -i
docker-compose exec nginx hostname -i
```

### Can't reach from host

```bash
# Service should be exposed in docker-compose.yml
ports:
  - "80:80"  # host:container

# If service not exposed, use container IP
docker-compose exec nginx hostname -i
curl http://<container-ip>:80
```

---

## Performance Debugging

### Check what's slow

```bash
# Time Django response
time curl http://localhost/

# Check database query count
docker-compose exec django python manage.py shell
>>> from django.db import connection
>>> from django.db import reset_queries
>>> reset_queries()
>>> # Run some code
>>> len(connection.queries)

# Profile with django-silk (optional)
pip install django-silk
# Add to INSTALLED_APPS, run migrations, check /silk/
```

### Monitor in real-time

```bash
# Watch logs for errors
watch 'docker-compose logs --tail 20 django | tail -20'

# Monitor stats
watch docker stats --no-stream

# Monitor system
htop  # Shows CPU, memory by process
```

---

## Logs Analysis

### Common Error Patterns

```bash
# Look for errors
docker-compose logs django | grep -i error

# Look for specific errors
docker-compose logs django | grep "OperationalError"

# Count errors
docker-compose logs django | grep -i error | wc -l

# Errors in last 10 minutes
docker-compose logs --since 10m | grep -i error

# Full error stack
docker-compose logs django | grep -A 10 "Traceback"
```

---

## Container Internals

### Access container shell

```bash
# Django container
docker-compose exec django /bin/bash

# Nginx container
docker-compose exec nginx /bin/sh

# Check installed packages
docker-compose exec django pip list

# Check Python version
docker-compose exec django python --version

# Check Django installation
docker-compose exec django python -m django --version
```

---

## Recovery Procedures

### Full cleanup and restart

```bash
# Stop everything
docker-compose down

# Remove images (if needed)
docker-compose down --rmi all

# Clean up volumes (be careful!)
docker volume prune

# Remove containers
docker container prune

# Remove images
docker image prune

# Full system cleanup
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache

# Start again
docker-compose up -d
```

### Backup before cleanup

```bash
# Export database
docker-compose exec postgres pg_dump -U noguser nogdb > backup.sql

# Copy static files
cp -r ./staticfiles ./staticfiles.backup

# Copy logs
cp -r ./logs ./logs.backup
```

---

## Health Check Debugging

### Test health endpoint

```bash
# From host
curl http://localhost/health/

# From nginx container
docker-compose exec nginx curl http://django:8000/

# Get response details
curl -v http://localhost/health/

# Check status code only
curl -o /dev/null -s -w "%{http_code}\n" http://localhost/health/
```

### Manually run health checks

```bash
# Django health check
docker-compose exec django curl -f http://localhost:8000/

# Nginx health check
docker-compose exec nginx wget --quiet --tries=1 --spider http://localhost/
```

---

## Prevention Tips

1. **Enable logging early**
   ```bash
   docker-compose logs -f > logs.txt &
   ```

2. **Monitor regularly**
   ```bash
   watch docker stats
   ```

3. **Keep backups**
   ```bash
   # Daily backup
   0 2 * * * docker-compose exec postgres pg_dump -U noguser nogdb > backup_$(date +%Y%m%d).sql
   ```

4. **Test before deploying**
   ```bash
   # Build images
   docker-compose build
   
   # Test locally
   docker-compose up
   docker-compose down
   ```

5. **Document your setup**
   - Keep notes on what works
   - Document any customizations
   - Version control everything

---

## Quick Reference Commands

```bash
# Essential commands
docker-compose ps                    # Status
docker-compose logs -f               # Live logs
docker-compose exec django bash      # Shell access
docker-compose restart               # Restart all
docker-compose down && docker-compose up -d  # Full restart

# Debugging commands
docker-compose logs django | head -50          # First 50 lines
docker-compose logs --tail 100 django          # Last 100 lines
docker stats --no-stream                       # Resource usage
docker-compose exec django python manage.py shell  # Django shell

# Maintenance commands
docker-compose exec django python manage.py migrate        # Migrations
docker-compose exec django python manage.py createsuperuser  # Admin
docker-compose exec django python manage.py collectstatic    # Static files
```

---

Need more help? Check logs first: `docker-compose logs -f`
