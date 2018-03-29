FROM python:3.6.1

RUN mkdir /code/
WORKDIR /code/
ADD ./requirements/ /code/requirements/

RUN pip install -r /code/requirements/development.txt

ENV DOCKERIZE_VERSION v0.5.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

RUN wget https://dl.minio.io/client/mc/release/linux-amd64/mc --output-document=/usr/local/bin/mc
RUN chmod +x /usr/local/bin/mc

ADD ./docker/development/docker-entrypoint.sh /tmp/docker-entrypoint.sh

ENTRYPOINT ["sh", "/tmp/docker-entrypoint.sh"]

