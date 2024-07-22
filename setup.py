#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from setuptools import find_packages, setup

# Installed by pip install pdr-backend
# or pip install -e .
install_requirements = [
    "black==24.4.2",
    "bumpversion",
    "ccxt==4.3.61",
    "coverage",
    "dash[testing]==2.17.1",
    "dash_bootstrap_components==1.6.0",
    "dateparser==1.2.0",
    "duckdb==1.0.0",
    "enforce_typing",
    "eth-account==0.11.0",
    "eth-keys==0.5.1",
    "eth-typing==4.4.0",
    "flask==3.0.3",
    "imblearn",
    "kaleido==0.2.1",
    "mypy==1.11.0",
    "numpy==2.0.1",
    "pandas==2.2.2",
    "pathlib",
    "plotly==5.22.0",
    "polars==1.1.0",
    "polars[timezone]",
    "pyarrow==16.1.0",
    "pylint==3.2.5",
    "pytest",
    "pytest-asyncio==0.21.1",
    "pytest-env",
    "pyyaml",
    "requests==2.32.3",
    "requests-mock==1.12.1",
    "scikit-learn==1.5.1",
    "statsmodels==0.14.2",
    "time_machine==2.14.2",
    "typeguard==4.3.0",
    "xgboost==2.1.0",
    "dash_bootstrap_components==1.6.0",
    "web3==6.20.0",
    "sapphire.py==0.2.3",
    "stopit==1.1.2",
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
