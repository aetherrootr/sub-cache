FROM python:3.13-slim

ENV ENV=prod
RUN mkdir -p /work /app

WORKDIR /app

COPY ./sub-cache.pyz /app/sub-cache.pyz
COPY ./dist /app/dist

RUN chmod +x /app/sub-cache.pyz

EXPOSE 8080

CMD ["python", "/app/sub-cache.pyz"]
