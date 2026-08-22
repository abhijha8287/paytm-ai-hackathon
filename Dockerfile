FROM python:3.11-slim

# openssl generates the self-signed HTTPS cert at container startup (see
# docker/entrypoint.sh) - phones on the same wifi need HTTPS for the mic
# and camera (getUserMedia is blocked on plain http:// for a LAN IP).
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY static ./static
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
