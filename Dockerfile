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

# Modify app/config.py to prioritize environment variables
# This ensures .env file is not required
RUN sed -i 's/load_dotenv()/load_dotenv(override=False)/' /app/config.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Set default config values (these will be overridden by environment variables if provided)
ENV PRIMARY_AI_SERVICE=azureopenai
ENV PRIMARY_MODEL=gpt-4o
ENV CLASSIFIER_AI_SERVICE=gemini
ENV CLASSIFIER_MODEL=gemini-1.0-pro
ENV CONTENT_MODERATION_ENABLED=True
ENV URL_SAFETY_CHECK_ENABLED=True
ENV DB_ROOT=/app/data
ENV LOG_LEVEL=INFO

# Print environment variables on startup for debugging
COPY <<-"EOF" /app/entrypoint.sh
#!/bin/bash
echo "Starting AIHacker Discord Bot..."
echo "Environment variables loaded successfully"
mkdir -p /app/data /app/logs
python main.py
EOF

RUN chmod +x /app/entrypoint.sh

# Command to run when the container starts
CMD ["/app/entrypoint.sh"] 