# Use official Python 3.11 slim image as a parent image
# "slim" means smaller image size, only essential packages
FROM python:3.11-slim

# Set working directory inside the container
# All commands below run from this foler
WORKDIR /app

# Copy requirements first (before copying all code)
# This is a docker optimization - explained below
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application code
COPY . .

# Tell Docker this container listens on port 8000 at runtime
EXPOSE 8000

# Command to run when container starts
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]