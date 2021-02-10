#!/usr/bin/env bash
SCRIPTPATH="$( cd "$(dirname "$0")" ; pwd -P )"
/usr/local/bin/pipenv run python "$SCRIPTPATH/update_data.py"