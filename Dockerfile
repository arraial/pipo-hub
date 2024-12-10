ARG PORT=8080
ARG PYTHON_VERSION=3.11.10
ARG BASE_OS=slim-bookworm
ARG BASE_IMAGE=python:${PYTHON_VERSION}-${BASE_OS}

FROM $BASE_IMAGE AS base

ARG POETRY_VERSION=1.8.4

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
    # fixes install error for cryptography package, as does locking cryptography version
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask interactive questions
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR="/tmp/poetry_cache" \
    \
    # requirements + virtual environment paths
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# prepend poetry and venv to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# install required system dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get --no-install-recommends install -y \
        ffmpeg \
    && pip install --upgrade pip setuptools wheel \
    && apt-get clean

# `builder-base` stage is used to build deps + create virtual environment
FROM base AS builder-base

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
    && apt-get clean \
    && pip install --ignore-installed distlib --disable-pip-version-check \
        cryptography==3.4.6 \
        poetry==$POETRY_VERSION \
    && poetry self add poetry-plugin-bundle

# copy project requirement files to ensure they will be cached
WORKDIR $PYSETUP_PATH
COPY pyproject.toml README.md ./
ARG PROGRAM_VERSION=0.0.0
RUN poetry version $PROGRAM_VERSION

# install runtime dependencies, internally uses $POETRY_VIRTUALENVS_IN_PROJECT
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry bundle venv --clear --without dev $VENV_PATH

FROM builder-base AS test
COPY --from=builder-base $VENV_PATH $VENV_PATH
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry bundle venv $VENV_PATH
COPY ./${APP_NAME} ./${APP_NAME}/
COPY ./tests ./tests
RUN poetry run pytest .

# `production` image used for runtime
FROM base AS production

# app configuration
ENV ENV=production \
    USERNAME=appuser \
    USER_UID=1000 \
    USER_GID=1000

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME
USER $USERNAME

COPY --from=builder-base --chown=$USERNAME:$USERNAME $VENV_PATH $VENV_PATH

# install application
COPY ./${APP_NAME} /${APP_NAME}/

EXPOSE $PORT
ENTRYPOINT "${VENV_PATH}/bin/python" "-m" "${APP_NAME}"
