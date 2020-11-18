from setuptools import setup, find_packages

setup(
    name='legimens',
    version='0.2.3',
    license='MIT',

    author = 'Danil Lykov',
    author_email = 'lkvdan@gmail.com',
    url='https://github.com/DaniloZZZ/legimens',

    packages=find_packages(),
    python_requires='>=3.6',

    install_requires = ['loguru', 'trio-websocket'],
    setup_requires = ['pytest-runner'],
    tests_require  = ['pytest'],

    test_suite='tests',
)
