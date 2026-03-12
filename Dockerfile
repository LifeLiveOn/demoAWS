FROM python:3.12-slim

WORKDIR /app

# install UV
RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "-b", "0.0.0.0:8000", "app.app:app"]