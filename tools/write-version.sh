#!/bin/bash

cd $(dirname $0)/..
git describe --tags --long --always | python -c 'from jinja2 import Template; print(Template("version = \"{{input}}\"").render(input=input()))' > version.py

