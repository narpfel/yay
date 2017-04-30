#!/usr/bin/env python3

from setuptools import find_packages, setup

requirements = [
    "setuptools",
    "PyYAML",
    "IHex",
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
    dependency_links=[
        "git+https://github.com/narpfel/IHex.git@master#egg=IHex-0.1.4"
    ],
    license="GPLv3",
    zip_safe=True,
    keywords='yay',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
