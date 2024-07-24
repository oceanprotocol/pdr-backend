#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from selenium.webdriver.chrome.options import Options

# pylint: disable=unused-import
from pdr_backend.sim.test.conftest import check_chromedriver


def pytest_setup_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    return options
