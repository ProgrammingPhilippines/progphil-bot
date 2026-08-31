FROM python:3.10-slim

# Build-time dependencies for C extensions (e.g. psycopg2, Levenshtein)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install modern Pip and Poetry into an isolated CLI location
RUN pip install --no-cache-dir -U pip setuptools \
    && pip install --no-cache-dir "poetry>=1.8.0"

WORKDIR /progphil-bot

# Leverage Docker layer caching: copy lockfiles first
COPY pyproject.toml poetry.lock ./

# Install project dependencies into Poetry's virtual environment
RUN poetry install --no-root --without dev

# Copy project source code after dependencies are installed
COPY README.md ./
COPY src ./src
COPY migrations ./migrations
COPY config ./config

# Install the root project package itself
RUN poetry install --without dev

# Run application using Poetry's virtual environment executable directly
CMD ["poetry", "run", "progphil"]