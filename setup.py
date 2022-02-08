#!/usr/bin/env python3  # pylint: disable=missing-docstring

from setuptools import setup

setup(name="bitwarden-to-keepass",
      version="v0.1.5",
      description="Convert BitWarden Vault into a KeePass Database (kdbx)",
      long_description=open('README.md', 'rb').read().decode('utf-8'),
      long_description_content_type="text/markdown",
      author="k3karthic",
      author_email="k3.karthic@protonmail.ch",
      url="https://github.com/k3karthic/bitwarden-to-keepass",
      download_url="https://github.com/k3karthic/bitwarden-to-keepass/tarball/v0.1.5",
      py_modules=["convert"],
      entry_points={
          'console_scripts': ['bw2kp=convert:main']
      },
      data_files=[('share/doc/bitwarden-to-keepass', ['README.md', 'LICENSE',
                                                      'CHANGELOG.md'])],
      license="MIT",
      install_requires=["pykeepass>=4.0.0"],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Topic :: Utilities',
      ],
      keywords=("bitwarden keepass"),
      )
