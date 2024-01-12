import os
import sys

# Add the root directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from pdr_backend.conftest_ganache import *  # pylint: disable=wildcard-import,wrong-import-position


@pytest.fixture(scope="session", autouse=True)
def set_test_env_var():
    previous = os.getenv("TEST")
    os.environ["TEST"] = "true"
    yield
    if previous is None:
        del os.environ["TEST"]
    else:
        os.environ["TEST"] = previous
