FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# Set Korea Standard Time (KST / UTC+9)
ENV TZ=Asia/Seoul

# Install Korean fonts and timezone data
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-nanum \
    fonts-noto-cjk \
    tzdata \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Web Dashboard Port
EXPOSE 8000

# Run FastAPI Web Dashboard + 24/7 Scheduler
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
