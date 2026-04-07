FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY data /app/data

RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["hr-server", "--host", "0.0.0.0", "--port", "8080"]
