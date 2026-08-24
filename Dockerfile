## Stage 1: Build the React frontend
FROM node:20-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
# Build with empty host/port — the frontend auto-detects same-origin in production
ENV VITE_GAME_HOST=""
ENV VITE_GAME_PORT=""
RUN npm run build

## Stage 2: Evennia game server
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc nginx netcat-openbsd psmisc postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pinned to the versions from the last known-good production build. Rebuilds
# are deterministic — an upstream release won't silently break a deploy that
# had no code changes. Bump these intentionally.
RUN pip install --no-cache-dir evennia==5.0.1 "django-allauth[socialaccount]==65.18.0" \
    psycopg2-binary==2.9.10 dj-database-url==2.3.0

# Copy the game code
COPY eldritchmush/ .

# Copy built React frontend into nginx serving directory
COPY --from=frontend-build /build/dist /usr/share/nginx/html

# Add /app to sys.path for EVERY Python process via a .pth file.
RUN echo "/app" > /usr/local/lib/python3.11/site-packages/eldritchmush_path.pth

ENV DJANGO_SETTINGS_MODULE=server.conf.settings

RUN cp /app/start.sh /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
