FROM python:3.13-slim

RUN mkdir -p /config /work /app

WORKDIR /app

COPY ./sub-cache.pyz /app/sub-cache.pyz

RUN chmod +x /app/sub-cache.pyz

EXPOSE 8080

CMD ["python", "/app/sub-cache.pyz"]
