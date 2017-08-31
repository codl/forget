uhh frick i forgot to write a readme hang on uhh

# forget

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/1780ac6071c04cbd9ccf75de0891e798)](https://www.codacy.com/app/codl/forget?utm_source=github.com&utm_medium=referral&utm_content=codl/forget&utm_campaign=badger)

its a thing that deletes your posts

it works with twitter and mastodon and maybe sometime in the future it will work with other services

it lives at <https://forget.codl.fr>

you can run your own if you want to, youll need postgresql and redis and python 3.6+ and yarn (recommended) or npm

```
$ # set up virtualenv (recommended)
$ virtualenv venv
$ source venv/bin/activate

$ # install requirements and set up config file
$ pip install -r requirements.txt
$ yarn || npm install
$ cp config.example.py config.py
$ $EDITOR config.py

$ # set up database schema
$ createdb forget
$ env FLASK_APP=forget.py flask db upgrade

$ # build assets
$ doit

$ # start web server and background worker
$ honcho start

$ # if you are doing development then you can try the dev procfile
$ honcho -f Procfile.dev start
```

the web server will listen on `127.0.0.1:42157`, you'll probably want to proxy with nginx or apache or what have you

sorry this readme sucks i forgot to write one before release

send me a tweet [@codl](https://twitter.com/codl) if you're having trouble or, to tell me you like it
