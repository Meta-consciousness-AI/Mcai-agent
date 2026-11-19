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

# 显式放入知识库，避免镜像内回退到旧数据
COPY config/corpus.json ./workspace/config/corpus.json
COPY data/kb.json ./workspace/data/kb.json
ENV MCAI_HOME=/app/workspace

EXPOSE 8080

# HTTP + /mcp（Streamable HTTP）；令牌由 MCAI_TOKEN 注入，为空时以空字符串传入
CMD ["sh", "-c", "mcai serve --host 0.0.0.0 --port ${PORT:-8080} --token \"${MCAI_TOKEN:-}\""]
