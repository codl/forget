![Forget](assets/promo.gif)

![User count](https://forget.codl.fr/api/badge/users)
![Maintenance status](https://img.shields.io/maintenance/yes/2022.svg)

[![Build status](https://img.shields.io/travis/codl/forget.svg)](https://travis-ci.org/codl/forget/)
[![Test coverage](https://img.shields.io/codecov/c/github/codl/forget.svg)](https://codecov.io/gh/codl/forget)

Forget is a post deleting service for Twitter, Mastodon, and Misskey.

You can run a copy of it on your server, or use the server run by the
maintainer at <https://forget.codl.fr/>


## Features

  * Delete your posts when they cross an age threshold.
  * Or keep your post count in check, deleting old posts when you go over.
  * Preserve old posts that matter by giving them a favourite or a reaction.
  * Set it and <i>forget</i> it. Forget works continuously in the background.

## Non-features

Forget is not a one-time purging tool. It is designed to prune your account
continuously, not quickly. If you need a lot of posts gone fast, you may want
to look for another more-suited tool.

## Running your own

### Requirements

* Postgresql
* Redis
* Python 3.6+
* Node.js 10+


### Set up venv

Setting up a venv will isolate Forget from your system's libraries and allow you to install
dependencies locally as a normal user. It's not necessary but it is recommended!

```
$ python -m venv venv
$ source venv/bin/activate
```

If you're using `zsh` or `fish` as a shell, substitute `venv/bin/activate` with
`venv/bin/activate.zsh` or `venv/bin/activate.fish`, respectively.

You will need to "activate" the venv in every new terminal before you can use
pip or any python tools included in dependencies (honcho, flask...)

### Download and install dependencies

```
$ pip install -r requirements.txt
$ npm install
```

Wow!! Exciting

### Create and complete config file

Gotta set up those, paths, and stuff.

```
$ cp config.example.py config.py
$ $EDITOR config.py
```

### Set up database schema

If you haven't started postgresql yet now would be a great time to do that.

```
$ createdb forget # if you havent created the DB yet
$ env FLASK_APP=forget.py flask db upgrade
```

### Build static assets

Gonna do it...!

```
$ doit
```

Done did it.

### Running

The included `Procfile` will run the app server and the background worker.
`honcho`, a `Procfile` runner, is included as a dependency:

```
$ honcho start
```

The application server will listen on `http://127.0.0.1:42157`.
You'll want to use your favourite web server to proxy traffic to it.

### Development

For development, you may want to use `Procfile.dev`, which starts flask in
debug mode and rebuilds the static assets automatically when they change

```
$ honcho -f Procfile.dev start
```

Or you could just look at `Procfile.dev` and run those things manually. It's up
to you.

You can run the (currently very incomplete) test suite by running `pytest`.
You'll need redis installed on your development machine, a temporary redis
server will be started and shut down automatically by the test suite.

## Contact

If you're having trouble with Forget, or if you're not having trouble but you
just want to tell me you like it, you can drop me a note at
[@codl@chitter.xyz](https://chitter.xyz/@codl) or
[codl@codl.fr](mailto:codl@codl.fr).

## Greetz

Thank you bea, for making ephemeral, inspiring me to make [limiter][], then this,
in an attempt to bring ephemeral with me everywhere. ☕

[limiter]: https://github.com/codl/limiter

Thank you to the kind folks who have emailed me to tell me Forget has made their
time on social media less stressful. 🌻
