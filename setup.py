import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "quarkchain",
    version = "0.0",
    author = "QuarkChain",
    author_email = "",
    description = ("QuarkChain"),
    license = "MIT",
    keywords = "QuarkChain,blockchain",
    url = "",
    packages=['quarkchain'],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 0 - Development",
        "License :: MIT License",
    ],
    install_requires=[
        'ecdsa',
        'ethereum',
        'leveldb',
        'numpy',
        'pysha3',
    ],
    python_requires='>=3.6'
)
