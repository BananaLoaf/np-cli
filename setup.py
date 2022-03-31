# Local
from setuptools import setup, find_packages

# External


# Project
from np_cli import PACKAGE_NAME, __version__


with open("README.md", "r") as file:
    LONG_DESCRIPTION = file.read()

# https://docs.python.org/2/distutils/setupscript.html
setup(name=PACKAGE_NAME,
      version=__version__,
      install_requires=[],
      packages=find_packages())
