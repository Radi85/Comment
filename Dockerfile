FROM python:3.10-slim-bullseye

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY . /code/
WORKDIR /code/

RUN pip install -r /code/test/example/requirements.txt \
    && python -m pip install django-comments-dab[markdown]
