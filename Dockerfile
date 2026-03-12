FROM python:3.12-slim

WORKDIR /app

# install UV
RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --no-dev

COPY app ./app

EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "app.app:app"]