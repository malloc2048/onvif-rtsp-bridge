FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    iputils-ping \
    net-tools \
    wget \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Install mediamtx (RTSP server)
ARG TARGETARCH
RUN ARCH=$(case ${TARGETARCH:-amd64} in amd64) echo "amd64" ;; arm64) echo "arm64v8" ;; *) echo "amd64" ;; esac) && \
    wget -q https://github.com/bluenviron/mediamtx/releases/download/v1.9.3/mediamtx_v1.9.3_linux_${ARCH}.tar.gz -O /tmp/mediamtx.tar.gz && \
    tar -xzf /tmp/mediamtx.tar.gz -C /usr/local/bin mediamtx && \
    rm /tmp/mediamtx.tar.gz && \
    chmod +x /usr/local/bin/mediamtx

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create logs directory
RUN mkdir -p /app/logs

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8080 8554

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${ONVIF_PORT:-8080}/onvif/device_service || exit 1

# Run the application
CMD ["python", "-m", "src.main"]
