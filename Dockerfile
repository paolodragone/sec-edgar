FROM astral/uv:python3.12-trixie-slim@sha256:760df02ce4a80b395949f5ac7bf9741c5123fb829d9b62092363bfdca0088059 AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Use the system Python interpreter.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-install-workspace --no-dev

COPY src/edgar/__init__.py src/edgar/__init__.py
COPY pyproject.toml .
COPY README.md .
COPY uv.lock .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

FROM python:3.12.13-slim-trixie@sha256:804ddf3251a60bbf9c92e73b7566c40428d54d0e79d3428194edf40da6521286

ARG DEBIAN_FRONTEND=noninteractive
ENV PATH="/app/.venv/bin:$PATH"
ENV TZ=Etc/UTC

# Packages required by WeasyPrint
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
    libjpeg-dev libopenjp2-7-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder --chown=app:app /app /app
COPY . /app

WORKDIR /app

ENTRYPOINT [ "python", "-m", "edgar.main" ]