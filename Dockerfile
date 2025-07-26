#   References: https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0

ARG PYTHON_VERSION=3.11-alpine  
ARG VIRTUAL_ENV=/instagram/.venv

# ---------- Build Stage ----------
FROM python:${PYTHON_VERSION} AS builder

RUN apk add --no-cache build-base libffi-dev openssl-dev

RUN pip install --no-cache-dir poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache  \
    FLASK_APP=app.main

WORKDIR /instagram

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root && rm -rf ${POETRY_CACHE_DIR}
# RUN poetry install --without dev --no-root && rm -rf ${POETRY_CACHE_DIR}


# ---------- Runtime Stage ----------
FROM python:${PYTHON_VERSION} AS runtime

WORKDIR /instagram

ARG VIRTUAL_ENV

ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "5", "app.main:app"]
