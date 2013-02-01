import os

from setuptools import setup, find_packages


setup(name='moz_inapp_pay',
      version='1.0.4',
      description='Utility for working with Mozilla in-app payments.',
      long_description='',
      author='Kumar McMillan',
      author_email='kumar.mcmillan@gmail.com',
      license='MPL 2.0 (Mozilla Public License)',
      url='https://github.com/kumar303/moz_inapp_pay',
      include_package_data=True,
      classifiers=[],
      packages=find_packages(exclude=['tests']),
      install_requires=[ln.strip() for ln in
                        open(os.path.join(os.path.dirname(__file__),
                                          'requirements.txt'))
                        if not ln.startswith('#')])
