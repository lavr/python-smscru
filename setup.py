#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

settings = dict()


# Publish Helper.
if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

settings.update(
    name='pysmscru',
    version='0.1',
    description='HTTP API client for smsc.ru',
    long_description=open('README.md').read(),
    author='Sergey Lavrinenko',
    author_email='s@lavrinenko.ru',
    url='https://github.com/lavr/python-smscru',
    py_modules= ['pysmscru',],
    scripts=['smscru.py', ],
    install_requires=[],
    license='BSD',
    classifiers=(
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        # 'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    )
)


setup(**settings)