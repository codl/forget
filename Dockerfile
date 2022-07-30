FROM python:3 AS builder
WORKDIR /usr/src/app
COPY . .

# install python stuff
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# build assets
RUN apt-get update -qq && apt-get install -qq nodejs npm
RUN npm install --save-dev
RUN doit

VOLUME ["/var/run/celery"]
