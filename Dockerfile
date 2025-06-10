FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends procps \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

 WORKDIR /app

# (except.dockerignore)
# COPY . .
COPY advertise_sender.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "advertise_sender.py"]
