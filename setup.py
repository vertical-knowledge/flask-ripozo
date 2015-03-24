from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from setuptools import setup, find_packages


version = '0.1.1'

setup(
    name='flask-ripozo',
    version=version,
    packages=find_packages(exclude=['tests', 'tests.*']),
    url='',
    license='',
    author='Tim Martin',
    author_email='tim.martin@vertical-knowledge.com',
    description='',
    install_requires=['ripozo', 'Flask'],
    test_suite='tests',
    tests_require=[
        'ripozo-tests',
        'tox'
    ]
)
