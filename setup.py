#!/usr/bin/env python3

from setuptools import setup

requirements = [
    "setuptools",
    "PyYAML",
]

setup(
    name='yay',
    packages=[
        'yay',
    ],
    package_dir={'yay': 'yay'},
    include_package_data=True,
    package_data={
        "yay": ["cpu_configurations/*.yml"],
    },
    install_requires=requirements,
    license="GPLv3",
    zip_safe=True,
    keywords='yay',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
