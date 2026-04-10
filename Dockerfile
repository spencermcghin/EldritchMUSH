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
    gcc nginx netcat-openbsd psmisc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir evennia "django-allauth[socialaccount]>=0.58"

# Copy the game code
COPY eldritchmush/ .

# Copy built React frontend into nginx serving directory
COPY --from=frontend-build /build/dist /usr/share/nginx/html

# Add /app to sys.path for EVERY Python process via a .pth file.
RUN echo "/app" > /usr/local/lib/python3.11/site-packages/eldritchmush_path.pth

ENV DJANGO_SETTINGS_MODULE=server.conf.settings

RUN cp /app/start.sh /start.sh && chmod +x /start.sh

CMD ["/start.sh"]
