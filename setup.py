import os

from setuptools import setup, find_packages


setup(name='moz_inapp_pay',
      version='1.0',
      description='Utility for working with Mozilla in-app payments.',
      long_description='',
      author='',
      author_email='kumar.mcmillan@gmail.com',
      license='BSD',
      url='',
      include_package_data=True,
      classifiers = [],
      packages=find_packages(exclude=['tests']),
      install_requires=['PyJWT',
                        'M2Crypto>=0.2.0'])
