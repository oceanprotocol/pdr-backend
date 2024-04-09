from os import getenv
from typing import Any, Dict


class CCXTExchangeMixin:
    @property
    def exchange_params(self) -> Dict[str, Any]:
        assert hasattr(self, "d")

        exc_d = {
            "apiKey": getenv("EXCHANGE_API_KEY"),
            "secret": getenv("EXCHANGE_SECRET_KEY"),
        }

        exc_d.update(self.d["exchange_only"])

        return exc_d
