# Multi-stage build for production Django application
FROM python:3.13-slim as builder

# Create a working directory
RUN mkdir /app
WORKDIR /app

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Install system dependencies for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy and install requirements
COPY ./requirements.txt /app/requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Final production stage
FROM python:3.13-slim

# Create a non-root user for security first (before creating directories)
RUN useradd -m -u 1000 appuser

# Create a working directory with proper permissions
RUN mkdir -p /app && chown -R appuser:appuser /app
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder and fix permissions
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Add user's local bin to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Copy the project files with proper permissions
COPY --chown=appuser:appuser . /app/

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Run gunicorn as the application server
CMD ["gunicorn", "--config", "/app/gunicorn_config.py", "nog_app.wsgi:application"]