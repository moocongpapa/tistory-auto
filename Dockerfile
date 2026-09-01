FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# Install Korean fonts for thumbnail generation
RUN apt-get update && apt-get install -y --no-install-recommends     fonts-nanum     fonts-noto-cjk     && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Web Dashboard Port
EXPOSE 8000

# Run FastAPI Web Dashboard + 24/7 Scheduler
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
