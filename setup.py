#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from setuptools import find_packages, setup

# Installed by pip install pdr-backend
# or pip install -e .
install_requirements = [
    "bumpversion",
    "ccxt",
    "coverage",
    "enforce_typing",
    "eth-account",
    "eth-keys",
    "matplotlib",
    "mypy",
    "numpy",
    "pandas",
    "pathlib",
    "pylint",
    "pytest",
    "pytest-asyncio",
    "pytest-env",
    "requests",
    "scikit-learn",
    "statsmodels",
    "types-requests",
    "web3",
    "sapphire.py",
    "ocean-contracts==2.0.0a14",  # install this last
]

# Required to run setup.py:
setup_requirements = ["pytest-runner"]

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

setup(
    author="oceanprotocol",
    author_email="devops@oceanprotocol.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    description="Predictoor backend",
    install_requires=install_requirements,
    name="pdr-backend",
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    packages=find_packages(
        include=[
            "pdr_backend",
        ]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    url="https://github.com/oceanprotocol/pdr-backend",
    # fmt: off
    # bumpversion needs single quotes
    version='0.0.14',
    # fmt: on
    zip_safe=False,
)
