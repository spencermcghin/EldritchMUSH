FROM python:3.11-slim

# bust cache: 2026-04-07
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc nginx netcat-openbsd psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir evennia

COPY . .

# Bake in PYTHONPATH and DJANGO_SETTINGS_MODULE so every subprocess
# (Portal, Server) can import 'server.conf.settings' without relying
# on sys.path propagation through nested Popen calls.
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=server.conf.settings

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
