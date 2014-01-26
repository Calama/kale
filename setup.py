# -*- coding: utf-8 -*-
"""
    kale setup script

    blah blah blah

    :copyright: 2013 Calama Consulting, written and maintained by uniphil
    :license: :) see http://license.visualidiot.com/
"""

from setuptools import setup


readme = open('README.md').read()


setup(
    name='kale',
    version='0.2.4',
    author='Philip Schleihauf',
    author_email='uniphil@gmail.com',
    url='https://github.com/Calama/kale',
    license=':) released by Calama Consulting',
    description='Tiny PyMongo model layer',
    long_description=readme,
    install_requires=['pymongo'],
    py_modules=['kale'],
)
