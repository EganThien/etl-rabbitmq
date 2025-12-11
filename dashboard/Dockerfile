FROM python:3.11-slim
WORKDIR /app

# Install cron for scheduled jobs
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY upload.html ./
COPY history.html ./
COPY rules.html ./
COPY scheduler.py ./
COPY start.sh ./

RUN mkdir -p /app/logs
RUN chmod +x /app/scheduler.py /app/start.sh

ENV PORT=8080
EXPOSE 8080

CMD ["/app/start.sh"]
