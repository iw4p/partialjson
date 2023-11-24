import os.path
import pathlib
import re

from setuptools import setup

PROJECT_NAME = 'partialjson'
# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


def get_property(prop):
    result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop),
                       open(os.path.join(PROJECT_NAME, '__init__.py')).read())
    return result.group(1)


setup(
    name='partialjson',
    version=get_property('__version__'),
    description='Parse incomplete or partial json',
    long_description=README,
    long_description_content_type="text/markdown",
    url=get_property('__url__'),
    author=get_property('__author__'),
    author_email=get_property('__author_email__'),
    license=get_property('__license__'),
    packages=['partialjson'],
)