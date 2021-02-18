#!/bin/bash

export AWS_CONTAINER_CREDENTIALS_RELATIVE_URI

pipenv run gunicorn app:server -b 0.0.0.0:8000 --workers=2 --threads=4 --worker-class=gthread --log-file=-
