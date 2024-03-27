#!/usr/bin/env python3
"""
A setuptools based setup module for the sample subsystem.
Author: Eirik Mulder (ecm0115@auburn.edu)
"""

from setuptools import setup

setup(name='sample_subsystem_api',
      version='0.1.0',
      description='KubOS API for communicating with the sample subsystem',
      py_modules=["sample_subsystem"],
      requires=["crc", "pyserial"]
      )
