# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11.0rc1

FROM python:${PYTHON_VERSION}-slim

LABEL fly_launch_runtime="flask"

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

# Force rebuild for training plan fix
COPY . .

# Create directory for database (database file is already included in COPY)
RUN mkdir -p /code/instance

EXPOSE 8080

# Use gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "wsgi:app"]

