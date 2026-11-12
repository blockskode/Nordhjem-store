# The Nordhjem API service for Cloud Run.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY api ./api
COPY data/products.jsonl data/product_images.json ./data/

# Cloud Run sets PORT (8080 by default).
CMD ["sh", "-c", "uv run --no-sync uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
