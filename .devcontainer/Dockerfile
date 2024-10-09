FROM mcr.microsoft.com/devcontainers/base:bullseye

ARG DEBIAN_FRONTEND=noninteractive
ARG USER=vscode

RUN DEBIAN_FRONTEND=noninteractive \
    && apt-get update \ 
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        git \
        git-secrets \
        libssl-dev \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        wget \
        curl \
        llvm \
        libncurses5-dev \
        xz-utils \
        tk-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libffi-dev \
        liblzma-dev \
        unzip \
        groff \
    && rm -rf /var/lib/apt/lists/* \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && sudo ./aws/install \
    && rm awscliv2.zip

# Python and poetry installation
USER $USER
ARG HOME="/home/$USER"
ARG PYTHON_VERSION=3.11

ENV PYENV_ROOT="${HOME}/.pyenv"
ENV PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${HOME}/.local/bin:$PATH"

RUN curl https://pyenv.run | bash \
    && pyenv install ${PYTHON_VERSION} \
    && pyenv global ${PYTHON_VERSION} \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && poetry config virtualenvs.in-project true

# Install pylint
# RUN pip install pylint

# Install dependecies for Opportunity Analyzer
RUN pip install pandas

# Install Black
# code formatter that automatically adjusts your code to comply with PEP 8, the Python style guide. 
# It's uncompromising but ensures consistency in code formatting across your project.
RUN pip install black

# Install mypy
# popular static type checker for Python. If you use type annotations, 
RUN pip install mypy

# Install boto3 type annotations
# Since boto3 (AWS SDK for Python) uses dynamic generation of classes, mypy cannot help much with it. 
# boto3-type-annotations provides the missing type annotations.
RUN pip install boto3-type-annotations-with-docs

# pytest: Testing framework that allows for the writing of simple and scalable test code for your Python projects.
RUN pip install pytest

# coverage: Tool for measuring code coverage of Python programs.
RUN pip install coverage

# safety: Checks your installed dependencies for known security vulnerabilities.
RUN pip install safety

# Node.js and NVM installation
ENV NVM_DIR /home/$USER/.nvm
ENV NODE_VERSION 18.18.2

RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV PATH $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

# Verify installations
RUN node --version
RUN npm --version

# Install Runway
RUN curl -L https://oni.ca/runway/2.4.3/linux -o /tmp/runway && \
    chmod +x /tmp/runway && \
    sudo mv /tmp/runway /usr/local/bin/runway && \
    runway --version

# Install Serverless Framework
RUN /bin/bash -c "source $HOME/.nvm/nvm.sh && npm install -g serverless@^2.58.0"

# Verify Serverless installation
RUN /bin/bash -c "source $HOME/.nvm/nvm.sh && serverless --version"

# Set the working directory within the Docker container
WORKDIR /app

# Copy only the pyproject.toml file to cache installed dependencies in docker layer
COPY pyproject.toml /app/

# Switch back to root to change permissions and then revert to the normal user
USER root
RUN chown -R $USER /app
USER $USER

# Install runtime dependencies using Poetry
RUN poetry install --no-interaction --no-ansi

# Optional: Copy the rest of your project code (Ensure you have proper .dockerignore to avoid copying unnecessary files)
COPY . /app/

# Echo a completion message
RUN echo "Dockerfile build complete. All tools and configurations have been set up."
