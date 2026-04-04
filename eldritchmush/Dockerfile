FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc nginx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir evennia

COPY . .

EXPOSE 8080

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
