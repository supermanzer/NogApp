#!/bin/bash
# Production startup script for Django application with Gunicorn

set -e  # Exit on any error

echo "Starting NogApp production server..."

# Wait for database to be ready (if using PostgreSQL)
# Uncomment if using PostgreSQL:
# echo "Waiting for database..."
# while ! nc -z ${DATABASE_HOST:-localhost} ${DATABASE_PORT:-5432}; do
#   sleep 1
# done
# echo "Database is ready!"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser from environment variables (for automated deployments)
echo "Setting up admin user..."
python manage.py create_superuser

# Collect static files for production
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Compile messages for i18n (if needed)
# python manage.py compilemessages

# Create cache table if using database cache
# python manage.py createcachetable

echo "Starting Gunicorn..."
# Start Gunicorn with the production configuration
exec gunicorn \
  --config /app/gunicorn_config.py \
  --access-logfile - \
  --error-logfile - \
  --log-level info \
  nog_app.wsgi:application


