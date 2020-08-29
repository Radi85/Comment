FROM python:3.8-alpine

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add bash \
    && apk add postgresql \
    && apk add postgresql-dev \
    && pip install psycopg2 \
    && apk add jpeg-dev zlib-dev libjpeg \
    && pip install Pillow \
    && apk del build-deps

WORKDIR /code/
COPY . /code/
WORKDIR /code/

RUN pip install -r /code/test/example/requirements.txt

RUN apk add --no-cache postgresql-libs

ENTRYPOINT ["/code/docker-entrypoint.sh"]
