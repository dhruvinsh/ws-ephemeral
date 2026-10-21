FROM python:3.14-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /app

# dependencies first, so this layer stays cached until the lock file changes
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# then the project itself, as a regular install so that the venv is self-contained
COPY src ./src
RUN uv sync --locked --no-dev --no-editable


FROM python:3.14-alpine

# the schedule runs in the local time, which is only configurable (TZ) with tzdata
RUN apk add --no-cache tzdata

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

CMD ["ws-ephemeral", "daemon"]
