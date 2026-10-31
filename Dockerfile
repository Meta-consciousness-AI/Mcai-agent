FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    PORT=8080 \
    MCAI_TOKEN=""

COPY pyproject.toml README.md LICENSE LICENSE-CONTENT ./
COPY mcai ./mcai
RUN pip install --no-cache-dir .

EXPOSE 8080

# HTTP + /mcp（Streamable HTTP）；令牌由 MCAI_TOKEN 注入
CMD ["sh", "-c", "mcai serve --host 0.0.0.0 --port ${PORT:-8080} --token ${MCAI_TOKEN:-}"]
