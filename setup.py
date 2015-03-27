import os

from setuptools import setup, find_packages


setup(name='mozpay',
      version='2.1.0',
      description="Make web payments with Mozilla's navigator.mozPay().",
      long_description='',
      author='Kumar McMillan',
      author_email='kumar.mcmillan@gmail.com',
      license='MPL 2.0 (Mozilla Public License)',
      url='https://github.com/mozilla/mozpay-py',
      include_package_data=True,
      classifiers=[],
      packages=find_packages(exclude=['tests']),
      install_requires=[ln.strip() for ln in
                        open(os.path.join(os.path.dirname(__file__),
                                          'requirements.txt'))
                        if not ln.startswith('#')])
