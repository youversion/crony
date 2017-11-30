# -*- coding: utf-8 -*-
"""Here's the beef. I should probably write better doc lines."""
import argparse
import configparser
import getpass
import logging
import subprocess
import os
import sys

import raven
import requests
from raven.handlers.logging import SentryHandler

__version__ = '0.2.0'


class CommandCenter(object):
    """Object to control running of commands."""

    config = None
    func = None
    logger = logging.getLogger('crony')
    opts = None
    sentry_client = None

    def __init__(self, opts):
        """Initialize the Command Center."""
        if opts.version:
            print(__version__)
            sys.exit(0)

        if not opts or not opts.cmd:
            raise RuntimeError('No command provided to run')
        else:
            self.opts = opts

        self.cmd = ' '.join(self.opts.cmd)

        # Load system wide options from config file
        config_msg = self.load_config(self.opts.config)

        # Setup Sentry Client before logging for SentryHandler
        if not self.opts.dsn:
            dsn = os.environ.get('SENTRY_DSN')
            if not dsn and self.config['crony']:
                dsn = self.config['crony'].get('sentry_dsn')
        else:
            dsn = self.opts.dsn
        if dsn:
            try:
                self.sentry_client = raven.Client(dsn, auto_log_stacks=True,
                                                  tags={'cron': self.cmd})
            except:  # noqa
                sentry_success = False
            else:
                sentry_success = True

        self.setup_logging()

        # Now that logging is setup
        if config_msg:
            self.logger.info(config_msg)
        if dsn and not sentry_success:
            self.logger.error(f'Error connecting to Sentry: {dsn}')

        self.setup_dir()
        self.setup_path()
        self.setup_venv()

        if self.opts.cronitor:
            self.func = self.cronitor
        else:
            self.func = self.run

    def cronitor(self):
        """Wrap run with requests to cronitor."""
        url = f'https://cronitor.link/{self.opts.cronitor}/{{}}'

        try:
            run_url = url.format('run')
            self.logger.debug(f'Pinging {run_url}')
            requests.get(run_url, timeout=self.opts.timeout)

        except requests.exceptions.RequestException as e:
            self.logger.exception(e)

        # Cronitor may be having an outage, but we still want to run our stuff
        output, exit_status = self.run()

        endpoint = 'complete' if exit_status == 0 else 'fail'
        try:
            ping_url = url.format(endpoint)
            self.logger.debug('Pinging {}'.format(ping_url))
            requests.get(ping_url, timeout=self.opts.timeout)

        except requests.exceptions.RequestException as e:
            self.logger.exception(e)

        return output, exit_status

    def load_config(self, custom_config):
        """Attempt to load config from file.

        If the command specified a --config parameter, then load that config file.
        Otherwise, the user's home directory takes precedence over a system wide config.
        Config file in the user's dir should be named ".cronyrc".
        System wide config should be located at "/etc/crony.conf"
        """
        self.config = configparser.ConfigParser()

        if custom_config:
            self.config.read(custom_config)
            return f'Loading config from file {custom_config}.'

        home = os.path.expanduser('~{}'.format(getpass.getuser()))
        home_conf_file = os.path.join(home, '.cronyrc')
        system_conf_file = '/etc/crony.conf'

        conf_precedence = (home_conf_file, system_conf_file)
        for conf_file in conf_precedence:
            if os.path.exists(conf_file):
                self.config.read(conf_file)
                return f'Loading config from file {conf_file}.'

        self.config['crony'] = {}
        return 'No config file found.'

    def log(self, output, exit_status):
        """Log given CompletedProcess and return exit status code."""
        output = output.decode('utf8')
        if output:
            self.logger.info(output)

        if exit_status != 0:
            self.logger.error(f'Error running command! Exit status: {exit_status}, {output}')

        return exit_status

    def run(self):
        """Run command and report errors to Sentry."""
        self.logger.debug(f'Running command: {self.cmd}')
        try:
            return subprocess.check_output(self.cmd, shell=True, stderr=subprocess.STDOUT), 0

        except subprocess.CalledProcessError as e:
            return e.output, e.returncode

    def setup_dir(self):
        """Change directory for script if necessary."""
        cd = self.opts.cd or self.config['crony'].get('directory')
        if cd:
            self.logger.debug(f'Adding cd to {cd}')
            self.cmd = f'cd {cd} && {self.cmd}'

    def setup_logging(self):
        """Setup python logging handler."""
        date_format = '%Y-%m-%dT%H:%M:%S'
        log_format = '%(asctime)s %(levelname)s: %(message)s'

        if self.opts.verbose:
            lvl = logging.DEBUG
        else:
            lvl = logging.INFO
            # Requests is a bit chatty
            logging.getLogger('requests').setLevel('WARNING')

        self.logger.setLevel(lvl)

        stdout = logging.StreamHandler(sys.stdout)
        stdout.setLevel(lvl)
        formatter = logging.Formatter(log_format, date_format)
        stdout.setFormatter(formatter)
        self.logger.addHandler(stdout)

        # Decided not to use stderr
        # stderr = logging.StreamHandler(sys.stderr)
        # stderr.setLevel(logging.ERROR)  # Error and above go to both stdout & stderr
        # formatter = logging.Formatter(log_format, date_format)
        # stderr.setFormatter(formatter)
        # self.logger.addHandler(stderr)

        log = self.opts.log or self.config['crony'].get('log_file')
        if log:
            logfile = logging.FileHandler(log)
            logfile.setLevel(lvl)
            formatter = logging.Formatter(log_format, date_format)
            logfile.setFormatter(formatter)
            self.logger.addHandler(logfile)

        if self.sentry_client:
            sentry = SentryHandler(self.sentry_client)
            sentry.setLevel(logging.ERROR)
            self.logger.addHandler(sentry)

        self.logger.debug('Logging setup complete.')

    def setup_path(self):
        """Setup PATH env var if necessary."""
        path = self.opts.path or self.config['crony'].get('path')
        if path:
            self.logger.debug(f'Adding {path} to PATH environment variable')
            self.cmd = f'export PATH={path}:$PATH && {self.cmd}'

    def setup_venv(self):
        """Setup virtualenv if necessary."""
        venv = self.opts.venv
        if not venv:
            venv = os.environ.get('CRONY_VENV')
            if not venv and self.config['crony']:
                venv = self.config['crony'].get('venv')
        if venv:
            if not venv.endswith('activate'):
                add_path = os.path.join('bin', 'activate')
                self.logger.debug(f'Venv directory given, adding {add_path}')
                venv = os.path.join(venv, add_path)
            self.logger.debug(f'Adding sourcing virtualenv {venv}')
            self.cmd = f'. {venv} && {self.cmd}'


def main():
    """Entry point for running crony.

    1. If a --cronitor/-c is specified, a "run" ping is sent to cronitor.
    2. The argument string passed to crony is ran.
    3. Next steps depend on the exit code of the command ran.
        * If the exit status is 0 and a --cronitor/-c is specified, a "complete" ping is sent
            to cronitor.
        * If the exit status is greater than 0, a message is sent to Sentry with the output
            captured from the script's exit.
        * If the exit status is great than 0 and --cronitor/-c is specified, a "fail" ping
            is sent to cronitor.
    """
    parser = argparse.ArgumentParser(
        description='Monitor your crons with cronitor.io & sentry.io',
        epilog='https://github.com/youversion/crony',
        prog='crony'
    )

    parser.add_argument('-c', '--cronitor', action='store',
                        help='Cronitor link identifier. This can be found in your Cronitor unique'
                        ' ping URL right after https://cronitor.link/')

    parser.add_argument('-e', '--venv', action='store',
                        help='Path to virtualenv to source before running script. May be passed'
                        ' as an argument or loaded from an environment variable or config file.')

    parser.add_argument('-d', '--cd', action='store',
                        help='If the script needs ran in a specific directory, than can be passed'
                        ' or cd can be ran prior to running crony.')

    parser.add_argument('-l', '--log', action='store',
                        help='Log file to direct stdout of script run to. Can be passed or '
                        'defined in config file with "log_file"')

    parser.add_argument('-o', '--config', action='store',
                        help='Path to a crony config file to use.')

    parser.add_argument('-p', '--path', action='store',
                        help='Paths to append to the PATH environment variable before running. '
                        ' Can be passed as an argument or loaded from config file.')

    parser.add_argument('-s', '--dsn', action='store',
                        help='Sentry DSN. May be passed or loaded from an environment variable '
                        'or a config file.')

    parser.add_argument('-t', '--timeout', action='store', default=10, help='Timeout to use when'
                        ' sending requests to Cronitor', type=int)

    parser.add_argument('-v', '--verbose', action='store_true', help='Increase level of verbosity'
                        ' output by crony')

    parser.add_argument('--version', action='store_true', help='Output crony version # and exit')

    parser.add_argument('cmd', nargs=argparse.REMAINDER, help='Command to run and monitor')

    cc = CommandCenter(parser.parse_args())

    sys.exit(cc.log(*cc.func()))
