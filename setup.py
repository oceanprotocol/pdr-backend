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
    "ccxt==4.3.11",
    "coverage",
    "dash==2.17.0",
    "enforce_typing",
    "eth-account==0.12.2",
    "eth-keys==0.5.1",
    "eth-typing==4.2.2",
    "flask==3.0.3",
    "freezegun==1.5.0",
    "imblearn",
    "kaleido==0.2.1",
    "mypy==1.10.0",
    "numpy==1.26.4",
    "pandas==2.2.2",
    "pathlib",
    "plotly==5.22.0",
    "polars==0.20.23",
    "polars[timezone]",
    "pyarrow==15.0.2",
    "pylint==3.1.0",
    "pytest",
    # pytest-asyncio: do not use dependabot to upgrade without checking lib changelog
    "pytest-asyncio==0.21.1",
    "pytest-env",
    "pyyaml",
    "requests==2.31.0",
    "requests-mock==1.12.1",
    "scikit-learn==1.4.2",
    "statsmodels==0.14.2",
    "types-pyYAML==6.0.12.20240311",
    "types-requests==2.31.0.20240406",
    "web3==6.17.2",
    "sapphire.py==0.2.2",
    "typeguard==4.2.1",
    "ocean-contracts==2.0.4",  # install this last
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
