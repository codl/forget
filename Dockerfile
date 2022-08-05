FROM python:3.10.6-bullseye AS pydeps
WORKDIR /usr/src/app

RUN python -m pip install --upgrade pip==22.2.2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


FROM pydeps AS pynodedeps

RUN apt-get update -qq && apt-get install -qq nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY package.json package-lock.json ./
RUN npm clean-install


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


FROM pynodedeps AS build

COPY --from=layer-cake / ./
RUN doit

FROM pydeps

COPY --from=build /usr/src/app ./

COPY .git/ .git/

ENV FLASK_APP=forget.py

VOLUME ["/var/run/celery"]
