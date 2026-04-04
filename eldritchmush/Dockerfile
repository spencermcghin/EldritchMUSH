FROM python:3.11-slim

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Evennia
RUN pip install --no-cache-dir evennia

# Copy game files
COPY . .

# Expose all Evennia ports
# 4000 = Telnet/MUD, 4001 = Web, 4002 = WebSocket
EXPOSE 4000 4001 4002

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
