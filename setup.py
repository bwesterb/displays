#!/usr/bin/env python

from setuptools import setup
from get_git_version import get_git_version

setup(name='displays',
        version=get_git_version(),
        description='Commandline tool to configure Mac OS X displaymodes',
        author='Bas Westerbaan',
        author_email='bas@westerbaan.name',
        url='http://github.com/bwesterb/displays/',
        packages=['displays'],
        package_dir={'displays': 'src'},
        entry_points = {
                'console_scripts': [
                        'displays = displays.main:main',
                ]
        }
)
