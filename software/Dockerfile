FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry

WORKDIR /software

COPY pyproject.toml ./
RUN poetry install --no-root --no-interaction

COPY . .
RUN poetry install --no-interaction

CMD ["poetry", "run", "pytest", "tests/", "-v"]
