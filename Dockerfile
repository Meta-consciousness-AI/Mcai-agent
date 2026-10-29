FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    MCAI_HOME=/app/demo

COPY pyproject.toml README.md LICENSE LICENSE-CONTENT ./
COPY mcai ./mcai
RUN pip install --no-cache-dir .

COPY docker/demo ./demo

CMD ["mcai-mcp"]
