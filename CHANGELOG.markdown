## future

* rewrote post-receive hook so it would play nice with versioneer

## v1.1.0

Released 2018-01-31

* three types of policies are now available for favs and media (keep only, delete only, ignore)
* a new input type was introduced to avoid having messy inline radio buttons
* sentry js init file now has 1 hour of caching
* fav and reblog count are now stored, for GH-7
* GH-17 reblogs are deleted regardless of media and favs
* mastodon instance popularity scoring has been simplified

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
