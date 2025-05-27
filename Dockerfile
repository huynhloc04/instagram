FROM python:3.11-slim

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache  \
    FLASK_APP=app.main

WORKDIR /instagram

COPY pyproject.toml poetry.lock ./

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY . .

RUN poetry install --without dev

EXPOSE 5000

CMD ["poetry", "run", "gunicorn", "--bind", "0.0.0.0:5000", "app.main:app"]
