FROM harbor.pg.innopolis.university/docker-hub-cache/astral/uv:python3.14-bookworm-slim

WORKDIR /app

COPY bot/pyproject.toml bot/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked

COPY bot /app

CMD ["uv", "run", "bot.py"]
