#!/usr/bin/env bash
set -e

dockerize -wait tcp://minio:9000

mc config host add minio $MINIO_HOST $MINIO_ACCESS_KEY $MINIO_SECRET_KEY

exec "$@"
