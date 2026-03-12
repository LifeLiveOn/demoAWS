FROM python:3.12-slim

WORKDIR /app

# install uv
RUN pip install --no-cache-dir uv

# copy dependency files first for docker layer caching
COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

# copy application code
COPY app ./app

EXPOSE 8080

CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:8080", "app.app:app"]