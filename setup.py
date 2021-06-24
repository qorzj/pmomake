# coding: utf-8
"""
pmomake
~~~~~~~~
CI/CD tool of Chongqing Parsec Corp.
Setup
-----
.. code-block:: bash
    > pip install pmomake
    > pmomake -h

"""

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path
from setuptools.command.install import install
import re
import ast

_version_re = re.compile(r'__version__\s+=\s+(.*)')
version = str(ast.literal_eval(
    _version_re.search(
        open('pmo/__init__.py').read()
    ).group(1)
))
here = path.abspath(path.dirname(__file__))


class MyInstall(install):
    def run(self):
        print("-- installing... --")
        install.run(self)

setup(
        name = 'pmomake',
        version=version,
        description='Makefile for PMO',
        long_description='\npip install pmomake\n\n'
                         'pmomake -h',
        url='https://pypi.python.org/pypi/pmomake',
        author='qorzj',
        author_email='inull@qq.com',
        license='MIT',
        platforms=['any'],

        classifiers=[
            ],
        keywords='pmomake pmo gantt',
        packages = ['pmo'],
        install_requires=['requests'],
        cmdclass={'install': MyInstall},
        entry_points={
            'console_scripts': [
                'pmomake = pmo.cli:entrypoint'
            ],
        },
    )
