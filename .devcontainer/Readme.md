# AWS Python Development Environment

## Table of Contents
- [AWS Python Development Environment](#aws-python-development-environment)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Setup](#setup)
    - [Development Container Features](#development-container-features)
      - [Python Version](#python-version)
    - [Installed Tools](#installed-tools)
    - [Workspace](#workspace)
    - [Usage](#usage)
    - [Contributing](#contributing)
    - [License](#license)

## Overview
README outlines setup of a development container with tools and libraries for Python AWS development.

## Getting Started

### Prerequisites
- Docker installed.
- Visual Studio Code (VS Code) installed.
- VS Code [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension installed.

### Setup
1. **Clone the Repository:**
    ```shell
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2. **Open in a Dev Container:**
- Open VS Code.
- Run the Remote-Containers: Open Folder in Container... command and select your project folder.

### Development Container Features
#### Python Version
Python 3.11 installed.

### Installed Tools
- AWS CLI: Command-line tool for AWS services.
- pylint: Python static code analysis tool.
- black: Uncompromising Python code formatter.
- mypy: Optional static type checker for Python.
- boto3-type-annotations: Type annotations for boto3.
- pytest: Testing framework for Python.
- coverage: Tool for measuring code coverage of Python programs.
- safety: Checks dependencies for known security vulnerabilities.

### Workspace
- Working directory in container is /app.
- pyproject.toml copied first to cache dependencies.
- Rest of application code located within /app directory.

### Usage
- Open project in VS Code, development container starts automatically.
- Installed tools are ready for use in development workflow.

### Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

### License
This project is licensed under the MIT License - see the LICENSE.md file for details.