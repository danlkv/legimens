from setuptools import setup, find_packages

setup(
    name='legimens',
    version='0.1.3',
    license='MIT',

    packages=find_packages(),
    python_requires='>=3.6',

    install_requires = ['loguru'],
    setup_requires = ['pytest-runner'],
    tests_require  = ['pytest'],

    test_suite='tests',
)
