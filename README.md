# pipo_hub
[![License](https://img.shields.io/github/license/arraial/pipo-hub)](https://opensource.org/licenses/MIT)
[![Build](https://github.com/arraial/pipo-hub/actions/workflows/docker.yml/badge.svg)](https://github.com/arraial/pipo-hub/actions/workflows/docker.yml)
[![Version](https://img.shields.io/github/v/tag/arraial/pipo-hub)](https://github.com/arraial/pipo-hub/releases)
[![Docker Image](https://img.shields.io/docker/image-size/arraial/pipo_hub/latest)](https://hub.docker.com/r/arraial/pipo_hub)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Sphinx](https://img.shields.io/badge/Docs-Sphinx-%230000?style=flat&logo=sphinx&color=%230A507A)](https://www.sphinx-doc.org/)

Pipo service responsible for user interaction and Discord server connection.

## Installation

### Runtime prerequisites
The application is compatible with Windows and Linux based systems.
[Docker](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/) are assumed to be installed and configured.

### Development
One may leverage VS Code Devcontainer for a simplified setup or other suitable option, as describbed in [Manual Setup](#manual).

#### Visual Studio Devcontainer
Devcontainer functionality can be used by choosing option `Dev Containers: Open Folder in Container...` in VS Code.

#### Manual Setup
For these guiding steps a [compatible version](pyproject.toml) of Python is assumed to be installed.

In case poetry is not locally installed:
```bash
make poetry_setup
```
To setup the development environment and being able to run the test suite do:
```bash
make dev_setup
```

Build the app container image with:
```bash
make image
```

For additional help try:
```bash
make help
```

## How to run

### Test suite
Before running the suite make sure file `/tests/.secrets.yaml` was created and filled based on the available [example](.secrets.example.yaml).

```bash
make test
```

### Containerized application
Before running the following command make sure `.env` was created and filled based on the available [example](.env.example).

Start the container with
```bash
make run_image
```

## License
This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.
