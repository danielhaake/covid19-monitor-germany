FROM ubuntu:20.04

LABEL maintainer='https://www.linkedin.com/in/daniel-haake/'

COPY . /app
WORKDIR /app

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 python3-pip python3-distutils\
      openjdk-11-jdk \
      poppler-utils libpoppler-dev libpoppler-cpp-dev build-essential pkg-config python-dev && \
    pip3 install pipenv && \
    pipenv install && \
    rm -rf /root/.cache && \
    apt-get -y purge libpoppler-cpp-dev build-essential pkg-config python-dev python3-pip && \
    apt-get -y autoremove --purge && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

CMD ["pipenv", "run", "python", "update_data.py"]