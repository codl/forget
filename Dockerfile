FROM python:3.10-bullseye AS deps
WORKDIR /usr/src/app

RUN python -m pip install --upgrade pip==22.2.2
RUN apt-get update -qq && apt-get install -qq nodejs npm

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY package.json package-lock.json ./
RUN npm install --save-dev


FROM scratch AS layer-cake
WORKDIR /

COPY *.py setup.cfg rollup.config.js ./
COPY assets assets
COPY components components
COPY libforget libforget
COPY migrations migrations
COPY routes routes
COPY static static
COPY templates templates


FROM deps

COPY --from=layer-cake / ./
RUN doit

ENV FLASK_APP=forget.py

VOLUME ["/var/run/celery"]
