from setuptools import setup, find_packages

setup(
    name='stockcon',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'requests',
        'inquirer',
        'matplotlib',
        'colorama'
    ],
    entry_points={
        'console_scripts': [
            'stockcon = app:main'
        ]
    }
)
