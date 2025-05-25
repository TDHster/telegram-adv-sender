FROM python:3.11-slim

WORKDIR /app

# (except.dockerignore)
# COPY . .
COPY advertise_sender.py .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "advertise_sender.py"]
