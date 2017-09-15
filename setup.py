# -*- coding: utf-8 -*-
"""setuptools control."""

import re
from setuptools import setup


version = re.search(
    "^__version__\s*=\s*'(.*)'",
    open('crony/crony.py').read(),
    re.M
).group(1)

with open('README.md', 'rb') as readme:
    long_descr = readme.read().decode('utf-8')

zip_file = f'https://github.com/youversion/crony/archive/{version}.zip'

setup(
    author='Brad Belyeu',
    author_email='brad.belyeu@life.church',
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities'
    ],
    description='Python command line application bare bones template.',
    download_url=zip_file,
    entry_points={'console_scripts': ['crony = crony.crony:main']},
    license='MIT',
    long_description=long_descr,
    install_requires=[
        'raven>=6.1.0',
        'requests>=2.18.4',
    ],
    keywords=['cron', 'monitoring', 'sentry.io', 'cronitor.io'],
    name='crony',
    packages=['crony'],
    platforms=['unix', 'mac'],
    url='https://github.com/youversion/crony',
    version=version,
)
