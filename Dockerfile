FROM python:3.12-slim

# System deps for Pillow (jpeg, zlib) and python-magic (libmagic)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        libmagic1 \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copy the rest of the app
COPY . /app

# Ensure runtime data dir exists (bind-mounted in compose)
RUN mkdir -p /app/backend/data

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=backend.app \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Use gunicorn in prod, fall back to flask dev server if needed
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "-k", "gthread", "--threads", "8", "--timeout", "120", "backend.app:app"]
