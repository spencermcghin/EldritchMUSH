FROM python:3.11-slim

# bust cache: 2026-04-06
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc nginx netcat-openbsd psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir evennia

COPY . .

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
