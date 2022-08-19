# syntax=docker/dockerfile:1.4.2

FROM python:3.10.6-bullseye AS pydeps
WORKDIR /usr/src/app

RUN --mount=type=cache,target=/root/.cache/pip/http pip install --upgrade pip==22.2.2

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip/http pip install -r requirements.txt


FROM pydeps AS pynodedeps

RUN rm -f /etc/apt/apt.conf.d/docker-clean &&\
    echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' \
    > /etc/apt/apt.conf.d/keep-cache
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update -qq && apt-get install -qq nodejs npm

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm clean-install


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
