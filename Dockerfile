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

#COPY test/example/requirements.txt ./test/example/requirements.txt
RUN pip install -r /code/test/example/requirements.txt

RUN apk add --no-cache postgresql-libs


#RUN python manage.py migrate
#RUN python manage.py create_initial_data
#CMD ["python", "manage.py", "migrate"]
#CMD ["python", "manage.py", "create_initial_data"]
ENTRYPOINT ["/code/docker-entrypoint.sh"]
