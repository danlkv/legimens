
from setuptools import setup, find_packages

setup(
    name='hosta',
    version='0.1',
    license='MIT',

    packages=find_packages(),
    python_requires='>=3.7',

    install_requires = ['loguru'],
    setup_requires = ['pytest-runner'],
    tests_require  = ['pytest'],

    test_suite='tests',
)
