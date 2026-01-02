ARG APP_VERSION=0.0.0
ARG PORT=8080
ARG PYTHON_VERSION=3.13
ARG BASE_OS=slim-bookworm
ARG BASE_IMAGE=python:${PYTHON_VERSION}-${BASE_OS}

ARG UV_VERSION=0.9.18
ARG FFMPEG_VERSION=8.0.1

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM mwader/static-ffmpeg:${FFMPEG_VERSION} AS ffmpeg

FROM $BASE_IMAGE AS base

ENV APP_NAME="pipo_hub" \
    # python
    PYTHON_VERSION=${PYTHON_VERSION} \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # uv
    UV_PYTHON_INSTALL_DIR=/python \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR="/tmp/uv_cache" \
    UV_PYTHON_PREFERENCE=only-managed \
    \
    # requirements + virtual environment paths
    PYSETUP_PATH="/app" \
    VENV_PATH="/app/.venv" \
    VENV_BIN="/app/.venv/bin"

# prepend venv to path
ENV PATH="$VENV_BIN:$PATH"

# install required system dependencies
COPY --from=ffmpeg /ffmpeg /ffprobe /usr/local/bin/

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean

# `builder-base` stage is used to build deps + create virtual environment
FROM base AS builder-base

COPY --from=uv /uv /uvx /bin/

COPY --from=ffmpeg /ffmpeg /ffprobe /usr/local/bin/

# install required system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
    build-essential \
    libc-dev \
    # discord.py[voice] dependencies
    python3-dev \
    libffi-dev \
    libnacl-dev \
    libssl-dev \
    && apt-get clean

WORKDIR $PYSETUP_PATH

COPY pyproject.toml README.md ./

# install runtime dependencies
RUN --mount=type=cache,target=$UV_CACHE_DIR \
    uv sync --no-install-project --no-dev --no-editable

# install application
COPY ./${APP_NAME} ./${APP_NAME}/
RUN --mount=type=cache,target=$(UV_CACHE_DIR) \
    uv sync --all-extras --no-dev --no-editable

FROM builder-base AS test
ARG APP_VERSION
RUN --mount=type=cache,target=$UV_CACHE_DIR uv sync --group dev
COPY ./tests ./tests/
ENV PIPO_VERSION=${APP_VERSION}
ENTRYPOINT [ "uv", "run", "pytest", "-m", "not wip" ]

# `production` image used for runtime
FROM gcr.io/distroless/python3-debian12:nonroot AS production
ARG APP_VERSION
COPY --from=ffmpeg --chown=nobody:nobody /ffmpeg /ffprobe /usr/local/bin/

ENV ENV=production \
    APP_NAME="pipo_hub" \
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # requirements + virtual environment paths
    PYSETUP_PATH="/app" \
    VENV_BIN="/app/.venv/bin" \
    PIPO_VERSION=${APP_VERSION}

# prepend venv to path
ENV PATH="$VENV_BIN:$PATH"
COPY --from=builder-base --chown=nobody:nobody $PYSETUP_PATH $PYSETUP_PATH
WORKDIR $PYSETUP_PATH
COPY --chown=nobody:nobody ./scripts/healthcheck.py .
EXPOSE $PORT
HEALTHCHECK --interval=10s --timeout=5s --start-period=3s --retries=3 \
    CMD ["python", "healthcheck.py"]
ENTRYPOINT ["python", "-m", "pipo_hub"]
