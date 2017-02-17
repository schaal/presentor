#!/usr/bin/python3

from setuptools import setup, find_packages

setup(
    name="Presentor",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'gui_scripts': ['presentor=presentor.presentor:main']
    },
)
