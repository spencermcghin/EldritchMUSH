FROM python:3.11-slim

# bust cache: 2026-04-07
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc nginx netcat-openbsd psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir evennia

COPY . .

# Add /app to sys.path for EVERY Python process via a .pth file.
# This is more reliable than PYTHONPATH because getenv() in the Portal's
# amp_server.py OVERRIDES PYTHONPATH with sys.path — if /app somehow
# drops out of the Portal daemon's sys.path, the Server subprocess won't
# have it either and 'import server' (needed by evennia.utils.utils →
# Django settings → server.conf.settings) will fail.
# .pth files are processed at Python startup unconditionally.
RUN echo "/app" > /usr/local/lib/python3.11/site-packages/eldritchmush_path.pth

ENV DJANGO_SETTINGS_MODULE=server.conf.settings

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
