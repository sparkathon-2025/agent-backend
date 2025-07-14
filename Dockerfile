FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libportaudio2 libportaudiocpp0 portaudio19-dev \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "main.py"]
