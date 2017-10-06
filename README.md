# Crony

Cron monitoring tool. It works well with cronitor.io & sentry.io
Cronitor.io can help you know if the tool doesn't start or end correctly. Or if it takes an
abnormally long time to complete.
Sentry.io helps debugging by giving stack traces when your cron code fails.

## Getting Started

This tool currently requires Python 3.6 or higher. There's a current issue to add Python 2
support.

If you're on a Mac, it's as simple as running

```
brew install python3
```

Or using whatever package manager for your system.

### Prerequisites

To get the benefit of [Cronitor.io](https://cronitor.io) integration. You'll need to sign up for
an account with them and setup a new "Cron job" monitor. When you setup your monitor, you'll
receive a link like

```
https://cronitor.link/6gVGE7/{ENDPOINT}
```

The alphanumeric string after "https://cronitor.link/" and before the endpoint is your Cronitor
unique identifier. You'll need to pass that to ``crony`` with --cronitor to integrate the cron
monitoring with cronitor.io.

To integration crony with Sentry.io for debugging & error tracking, you'll need to create an
account at [Sentry.io](https://sentry.io). After creating an account, you can setup a project
for your crons. Sentry will give you a DSN url that you'll need to integration with crony.
You can then specify your DSN when calling ``crony`` with ``--dsn``, or with a SENTRY_DSN
environment variable, or by placing it inside a config file.

### Installing

Simply install with

```
pip install crony
```

To get a list of options use

```
crony --help
```

Crony can wrap any shell command, try this

```
crony echo "hello world"
```

View the [wiki](https://github.com/youversion/crony/wiki) for environment variables and
configuration file options.

## Running the tests

There's a current issue to write unit tests.

### And coding style tests

New commits must pass pep8 & flake8 standards.
The only allowed exception is [pep8 line length](https://www.python.org/dev/peps/pep-0008/#maximum-line-length)
is allowed to be up to 99 characters.

```
pep8 . --max-line-length=99
```

Should yield 0 errors.

```
flake8 .
```

Should also yield 0 errors.

## Built With

* [Raven](https://github.com/getsentry/raven-python) - Python client for Sentry
* [Requests](http://docs.python-requests.org/en/master/) - Requests: HTTP for Humans

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process
for submitting pull requests.

## Versioning

Ideally we'll use [SemVer](http://semver.org/) for versioning.
For the versions available, see the [tags on this repository](https://github.com/youversion/crony/tags).

## Authors

* **Brad Belyeu** - *Initial work* - [bbelyeu](https://github.com/bbelyeu)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

* Thanks to [PurpleBooth](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2) for the README template
* Thanks to [Jan-Philip](https://gehrcke.de/2014/02/distributing-a-python-command-line-application/) for the great blog post.
