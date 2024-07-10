FROM python:3.10-slim

ARG token

# necessary env vars for poetry to work properly
ENV token=$token \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.3.2

# Install Poetry 1.3.2 via pip
RUN pip install -U pip \
    && apt-get update \
    && apt-get install gcc -y \
    && apt install -y libpq-dev python3-dev \
    && pip install "poetry==1.3.2" \
    && pip install setuptools>=65.5.1
ENV PATH="${PATH}:/root/.poetry/bin"

# Install Poetry dependencies
WORKDIR /progphil-bot
COPY poetry.lock pyproject.toml ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy source code
COPY . /progphil-bot

# Run the bot
CMD ["poetry", "run", "python", "src/bot/main.py"]
