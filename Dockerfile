FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt pytest.ini README.md ./
COPY src ./src
COPY tests ./tests
COPY docs ./docs

RUN python -m pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "mlstore_lite.experiments.run_all", "--quick"]
