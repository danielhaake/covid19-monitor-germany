#!/bin/bash

export AWS_CONTAINER_CREDENTIALS_RELATIVE_URI
pipenv run python update_data.py
