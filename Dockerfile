# Use official Python image (Debian-based)
FROM python:3.11-bullseye

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory inside container
WORKDIR /app

# Install system dependencies required for:
# Pillow (images), PostgreSQL, EasyOCR/OpenCV
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        libgl1-mesa-glx \
        libglib2.0-0 \
        apt-transport-https \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to leverage Docker cache)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (including already collected static files)
COPY . /app/

# Expose Django default port
EXPOSE 8000

# Run migrations and start Django development server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
