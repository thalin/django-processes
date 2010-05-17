#!/usr/bin/env python
'''
Created on May 17 2010

@author: tpharris

Setup script for django-processes
'''
from distutils.core import setup

setup(name="django-processes",
      version="0.5",
      description="Long-running task queue for Django",
      author="Zeke Harris",
      author_email="thalin@gmail.com",
      url="http://github.com/thalin/django-processes",
      packages=["processes"],
     )

