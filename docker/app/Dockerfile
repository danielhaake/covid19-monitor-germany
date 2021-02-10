from python:3.8

LABEL maintainer='https://www.linkedin.com/in/daniel-haake/'

COPY . /app
WORKDIR /app

RUN apt-get update && apt-get install -y \
    poppler-utils libpoppler-dev libpoppler-cpp-dev build-essential pkg-config python-dev

RUN pip install pipenv

RUN pipenv install

EXPOSE 8000

CMD ["pipenv", "run", "gunicorn", "app:server", "-b", "0.0.0.0:8000"]