FROM openjdk:slim
COPY --from=python:3.8 / /

LABEL maintainer='https://www.linkedin.com/in/daniel-haake/'

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    poppler-utils libpoppler-dev libpoppler-cpp-dev build-essential pkg-config python-dev

RUN pip install pipenv

RUN pipenv install

CMD ["pipenv", "run", "python", "update_data.py"]