# Use the existing Dockerfile as base
FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    build-base \
    libffi-dev \
    openssl-dev \
    git \
    curl \
    vim \
    nano \
    htop \
    mysql-client \
    redis

# Install Poetry
RUN pip install --no-cache-dir poetry==1.4.2

# Set Poetry environment variables
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    FLASK_APP=app.main

WORKDIR /instagram

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry install --no-root && rm -rf ${POETRY_CACHE_DIR}

# Copy the rest of the application
COPY . .

# Create a non-root user for development
RUN addgroup -g 1000 developer && \
    adduser -D -s /bin/bash -u 1000 -G developer developer

# Change ownership of the workspace
RUN chown -R developer:developer /instagram

# Switch to the developer user
USER developer

# Expose ports
EXPOSE 8000 5678

# Default command (can be overridden by docker-compose)
CMD ["poetry", "run", "python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"] 