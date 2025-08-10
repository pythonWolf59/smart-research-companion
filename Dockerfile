FROM python:3.11-slim

# Install any OS-level dependencies your Python packages need
RUN apt-get update && apt-get install -y gcc numpy scipy libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the appropriate port
EXPOSE 8000

# Launch your app (assuming app/main:app is your entrypoint)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
