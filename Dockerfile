FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md /app/
COPY src /app/src
COPY templates /app/templates
COPY examples /app/examples
RUN pip install --no-cache-dir -e ".[dev]"

ENTRYPOINT ["path-term-kit"]

