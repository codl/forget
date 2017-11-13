## v1.0.0

* image proxy now respects max-age from cache-control header
* image proxy now stores a handful of whitelisted headers
* privacy policy moved to its own page
* only one copy of each task+args can run at once
* fix Error returning to forget after cancelling authorization #14
* a whole lot of trying to not hit rate limits
* removed flask-limiter
* a whole buncha minor changes and fixes that i don't remember because i'm writing this after the fact 🤷

## v0.0.10

* a test suite (it only tests libbrotli for now)
* an image proxy for those avatars that are served over http not https
* show a message to the user when their account has been
  administratively disabled to explain why
* whjole lot of quality of life improvements
* whole lot of bug fixes
* some stylistic changes

## v0.0.9

* logged in page now shows time of last delete and next delete
* enabling/disabling doesnt require a refresh anymore
* security enhancements (A+ on moz observatory binchhhhh)
* bug fixes etc

## v0.0.8

* quick log-in buttons for popular mastodon instances
* add csrf tokens
* bug fixes

## v0.0.7

* add option for mastodon users to preserve direct messages (enabled by default)
* removed storing the posts' bodies. it was convenient for debugging early on but now it's kinda iffy privacy wise
* various fixes for mastodon

## before v0.0.7

idk
