#
# Copyright 2024 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
class MockOrder(dict):
    def __str__(self):
        return f"mocked order: {self.get('amount')} {self['pair_str']}"
