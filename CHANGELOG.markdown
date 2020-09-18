## vNEXT

* fix: wording on "favourited posts" is unclear
  <https://github.com/codl/forget/pull/366>

## v2.0.0

Released 2019-09-13

* fix: newer twitter accounts not fetching new posts past the initial historical fetch
  <https://github.com/codl/forget/pull/254>
* fix: fetching task not getting rescheduled properly when doing the initial historic fetch
  <https://github.com/codl/forget/pull/264>
* BREAKING: disabled tweet archive upload since twitter has dropped support for them
  <https://github.com/codl/forget/pull/265>

## v1.6.1

Released 2019-07-23

* increased frequency of refresh jobs
* version number in footer now links to changelog instead of commit log
* updated about page. less negative, more succint, clarifies that forget is not a purging tool

## v1.5.3

Released 2019-07-11

* fix: everything related to mastodon broken because of a typo

## v1.5.2

Released 2019-07-11

* fix: stock user agent when querying mastodon servers

## v1.5.1

Released 2019-05-02

* fix: proxied avatars not working in some environments
* dependency updates

## v1.5.0

Released 2019-03-15

* back off before hitting rate limit on mastodon instances
* tracking of used instances for the login buttons on the front page is now entirely client-side,
  avoiding a potential information disclosure vulnerability ([GH-175](https://github.com/codl/forget/issues/175))
* fix: fetch\_acc running multiple copies fetching the same posts
* internals: increased frequency of refresh jobs, decreased frequency of bookkeeping jobs

## v1.4.3

Released 2019-03-11

* documentation improvements
* fix: deadlock when refreshing or deleting from mastodon accounts ([GH-19](https://github.com/codl/forget/issues/19))
* fix: crash in fetch\_acc when user has no posts
* fix: not backing off if something crashes in refresh\_account
* fix: crashes when trying to refresh but no accounts have been created yet

## v1.4.2

Released 2019-02-24

* fix: implemented a more robust fetching algorithm, which should prevent accounts getting stuck with only a fraction of their posts fetched ([GH-13](https://github.com/codl/forget/issues/13))
* fix: picture tags having an extra comma
* fix: outdated joke in about page
* fix: posts' status not getting refreshed (ie whether or not they were faved, or deleted externally)
* internals: removed `x-` prefix from custom headers, as per [section 8.3.1 of RFC7231](https://httpwg.org/specs/rfc7231.html#considerations.for.new.header.fields)

## v1.4.1 (security update)

Released 2018-10-29

* updated requests to 2.20.0 ([CVE-2018-18074](https://nvd.nist.gov/vuln/detail/CVE-2018-18074))

## v1.4.0

Released 2018-10-06

* added warning when it looks like an archive is a full "Your Twitter data" archive

## v1.3.0

Released 2018-07-06

* implement exponential backoff

## v1.2.1

Released 2018-05-08

* limit number of log-in buttons to 5, and show up to 5 known instances

## v1.2.0

Released 2018-05-08

* remember a user's mastodon instances and let them log in in one click ([GH-36](https://github.com/codl/forget/issues/36))

## v1.1.3

Released 2018-04-25

* made radio strips more accessible
* unified button looks
* updated and cleaned up markup in README

## v1.1.2

Released 2018-04-25

* fixed crash when saving settings with JS disabled

## v1.1.1

Released 2018-04-19

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
