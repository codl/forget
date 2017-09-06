/*global Raven*/
Raven.config('{{sentry_dsn}}').install();
