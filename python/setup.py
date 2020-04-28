from setuptools import setup, find_packages

setup(
    name='legimens',
    version='0.2.0',
    license='MIT',

    packages=find_packages(),
    python_requires='>=3.6',

    install_requires = ['loguru', 'trio-websocket'],
    setup_requires = ['pytest-runner'],
    tests_require  = ['pytest'],

    test_suite='tests',
)
