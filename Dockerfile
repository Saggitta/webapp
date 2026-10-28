FROM python:3.14.10-slim-trixie@sha256:3cabfd7d7aaf394e6040e79fa1eec6ca1c52b74ed9188650472695d9a9326999
RUN apt-get update && apt-get install -y --no-install-recommends
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY . /app
WORKDIR /app
ENV UV_NO_DEV=1
RUN uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fastapi", "run", "app/main.py", "--port", "80"]