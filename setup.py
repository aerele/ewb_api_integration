# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in ewb_api_integration/__init__.py
from ewb_api_integration import __version__ as version

setup(
	name='ewb_api_integration',
	version=version,
	description='Implementation of Eway Bill API Integration for India',
	author='Aerele',
	author_email='admin@aerele.in',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
