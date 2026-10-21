FROM python:3.14-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# only the dependency manifests, so this layer stays cached until they change
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev


FROM python:3.14-alpine

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY src ./

CMD ["python3", "run.py"]
