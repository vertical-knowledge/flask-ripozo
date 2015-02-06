from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'VERSION')) as f:
    version = f.read().strip()

setup(
    name='flask-ripozo',
    version=version,
    packages=[], # TODO
    url='',
    license='',
    author='Tim Martin',
    author_email='tim.martin@vertical-knowledge.com',
    description='',
    install_requires=['ripozo', 'Flask']
)
