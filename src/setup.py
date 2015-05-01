# coding: utf-8

from setuptools import setup

setup(
    name='ikez',
    version='0.1.5',
    py_modules=['ikez'],
    install_requires=[
        'colorama==0.3.3',
        'semver==2.0.1',
        'python-dateutil==2.4.2'
    ],
    entry_points='''
        [console_scripts]
        ikez=ikez:main
    ''',
)