#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import pytest

from selenium import webdriver  # type: ignore[import-untyped]
from selenium.webdriver.chrome.options import Options  # type: ignore[import-untyped]
from selenium.common.exceptions import WebDriverException  # type: ignore[import-untyped]

logger = logging.getLogger("dependencies")


def pytest_setup_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return options


@pytest.fixture
def check_chromedriver():
    try:
        driver = webdriver.Chrome()
        driver.quit()
    except WebDriverException:
        message = """
            It seems that you don't have chromedriver installed on your system.
            Please install it by following the instructions at https://sites.google.com/a/chromium.org/chromedriver/.
            For ubuntu, you can install it using the following command: sudo apt-get install chromium-chromedriver.
            For Mac:
                - you can install it using the following command: brew install chromedriver.
                - go to chromedriver location and move it to /usr/local/bin/ using this command: sudo mv chromedriver /usr/local/bin/
                - change the file access mode to add execution permision using this command: sudo chmod +x /usr/local/bin/chromedriver
                - if a popup appears when running the tests, click on open and test should pass from now on
            For Windows, you can download the chromedriver from the link above and add it to your PATH.
            If you have chromedriver installed, make sure it is in your PATH.
        """

        logger.error(message)
