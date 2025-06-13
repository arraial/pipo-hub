ARG APP_VERSION=0.0.0
ARG PORT=8080
ARG PYTHON_VERSION=3.13.3
ARG BASE_OS=slim-bookworm
ARG BASE_IMAGE=python:${PYTHON_VERSION}-${BASE_OS}

ARG UV_VERSION=0.7.12
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM $BASE_IMAGE AS base

# python
ENV APP_NAME="pipo_hub" \
    PYTHON_VERSION=${PYTHON_VERSION} \
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # uv
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_CACHE_DIR="/tmp/uv_cache" \
    UV_PYTHON_DOWNLOADS=0 \
    \
    # requirements + virtual environment paths
    PYSETUP_PATH="/app" \
    VENV_PATH="/app/.venv" \
    VENV_BIN="/app/.venv/bin"

# prepend venv to path
ENV PATH="$VENV_BIN:$PATH"

# install required system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get --no-install-recommends install -y \
    ffmpeg \
    && apt-get clean

# `builder-base` stage is used to build deps + create virtual environment
FROM base AS builder-base
COPY --from=uv /uv /uvx /bin/

# install required system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y \
    build-essential \
    libc-dev \
    libssl-dev \
    # discord.py[voice] dependencies
    python3-dev \
    libffi-dev \
    libnacl-dev \
    && apt-get clean

# copy project requirement files to ensure they will be cached
WORKDIR $PYSETUP_PATH
COPY pyproject.toml README.md ./

# install runtime dependencies
RUN --mount=type=cache,target=$UV_CACHE_DIR \
    #    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-editable

# install application
COPY ./${APP_NAME} ./${APP_NAME}/

RUN --mount=type=cache,target=$(UV_CACHE_DIR) \
    uv sync --all-extras --no-editable

FROM builder-base AS test
ARG APP_VERSION
RUN --mount=type=cache,target=$UV_CACHE_DIR uv sync --group dev
COPY ./tests ./tests/
ENV PIPO_VERSION=${APP_VERSION}
RUN uv run pytest .
ENTRYPOINT [ "uv", "run", "pytest", "." ]

# `production` image used for runtime
FROM base AS production
ARG APP_VERSION
# app configuration
ENV ENV=production \
    USERNAME=appuser \
    USER_UID=1000 \
    USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
USER $USERNAME

COPY --from=builder-base --chown=$USERNAME:$USERNAME $PYSETUP_PATH $PYSETUP_PATH

EXPOSE $PORT
WORKDIR $PYSETUP_PATH
ENV PIPO_VERSION=${APP_VERSION}
COPY --chown=$USERNAME:$USERNAME ./scripts/healthcheck.py .
HEALTHCHECK --interval=10s --timeout=5s --start-period=3s --retries=3 \
    CMD ["python", "healthcheck.py"]
ENTRYPOINT "python" "-m" "${APP_NAME}"
