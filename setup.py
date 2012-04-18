#! /usr/bin/env python

from setuptools import setup, find_packages

setup(name="typeslower",
      version="0.1",
      author="Rory McCann",
      author_email="rory@technomancy.org",
      packages=['typeslower'],
      #install_requires=['Python Xlib'],
      entry_points = {
          'console_scripts': [
              'typeslower = typeslower:main',
          ]
      },
)
