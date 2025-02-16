FROM python:3.12-slim-bookworm

# Install essential system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Download and install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN chmod +x /uv-installer.sh && sh /uv-installer.sh && rm /uv-installer.sh

# Ensure uv is available in the PATH
ENV PATH="/root/.local/bin:$PATH"

# ✅ Create the /data folder
RUN mkdir -p /data

# Set up the application directory
WORKDIR /app

# Copy application files
COPY app.py /app
COPY tasksA.py /app
COPY tasksB.py /app

# Install FastAPI and Uvicorn
RUN pip install --no-cache-dir fastapi uvicorn

# Explicitly set the correct binary path and start the application
CMD ["/root/.local/bin/uv", "run", "app.py"]
