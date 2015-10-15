#!/usr/bin/env python3

from setuptools import setup, find_packages

requirements = [
    "setuptools",
    "PyYAML",
]

setup(
    name='yay',
    packages=find_packages(),
    package_dir={'yay': 'yay'},
    include_package_data=True,
    package_data={
        "yay": ["cpu_configurations/*.yml"],
    },
    entry_points={
        "console_scripts": [
            "yay=yay.__main__:main",
        ]
    },
    install_requires=requirements,
    license="GPLv3",
    zip_safe=True,
    keywords='yay',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
