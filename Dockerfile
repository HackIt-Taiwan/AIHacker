FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN groupadd -g 1000 botuser && \
    useradd -u 1000 -g botuser -s /bin/bash -m botuser

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R botuser:botuser /app

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set permissions for application files
RUN chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Create data and logs directories if they don't exist
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run when the container starts
CMD ["python", "main.py"] 