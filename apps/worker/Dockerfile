FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install standard security tools (nmap, etc would go here in real build)
# RUN apt-get update && apt-get install -y nmap

COPY . .

CMD ["python", "main.py"]
