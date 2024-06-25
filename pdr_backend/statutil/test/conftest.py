from selenium.webdriver.chrome.options import Options

# pylint: disable=unused-import
from pdr_backend.sim.test.conftest import check_chromedriver


def pytest_setup_options():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return options
