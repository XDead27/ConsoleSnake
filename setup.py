from setuptools import setup, find_packages

# Read the requirements from the requirements.txt file
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='ConsoleSnake',
    version='0.3.2.alpha',
    packages=find_packages(),
    install_requires=required,
)
